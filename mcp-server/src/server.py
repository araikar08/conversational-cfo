#!/usr/bin/env python3
"""
Poke MCP Server for Conversational Expense Tracking
Implements receipt OCR and conversational categorization workflow.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

import requests
from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Conversational CFO MCP Server")

# Environment variables
LAVA_FORWARD_TOKEN = os.getenv("LAVA_FORWARD_TOKEN")
LAVA_BASE_URL = os.getenv("LAVA_BASE_URL", "https://api.lavapayments.com/v1/forward")
POKE_API_KEY = os.getenv("POKE_API_KEY")

# Validate required environment variables
if not LAVA_FORWARD_TOKEN:
    raise ValueError("LAVA_FORWARD_TOKEN environment variable is required")
if not POKE_API_KEY:
    raise ValueError("POKE_API_KEY environment variable is required")

# Configure LLM clients with Lava proxy
ocr_llm = ChatOpenAI(
    model="gpt-4o",
    api_key=LAVA_FORWARD_TOKEN,
    base_url=f"{LAVA_BASE_URL}?u=https://api.openai.com/v1",
    temperature=0.3,
)

reasoning_llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=LAVA_FORWARD_TOKEN,
    base_url=f"{LAVA_BASE_URL}?u=https://api.openai.com/v1",
    temperature=0.7,
)

# In-memory state management
USER_STATES: Dict[str, Dict[str, Any]] = {}

# Lava cost tracking (per-user analytics)
USER_COSTS: Dict[str, Dict[str, Any]] = {}  # {user_id: {"total_cost": float, "receipts_processed": int, "history": []}}


# Pydantic models
class ReceiptInput(BaseModel):
    """Input model for receipt processing"""
    user_id: str = Field(..., description="Unique identifier for the user")
    message: str = Field(default="", description="Text message from user")
    image_url: Optional[str] = Field(None, description="URL of the receipt image")


class PokeReplyTool:
    """Custom tool for sending messages back to users via Poke API"""

    @staticmethod
    def send_message(user_id: str, message: str) -> str:
        """
        Send a message to the user via Poke API

        Args:
            user_id: User identifier
            message: Message content to send

        Returns:
            Confirmation string
        """
        try:
            logger.info(f"Sending message to user {user_id}: {message[:100]}...")

            response = requests.post(
                "https://poke.com/api/v1/inbound-sms/webhook",
                headers={
                    "Authorization": f"Bearer {POKE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "user_id": user_id,
                    "message": message
                },
                timeout=10
            )

            response.raise_for_status()
            logger.info(f"Message sent successfully to {user_id}")
            return f"Message sent to user {user_id}: {message}"

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send message via Poke API: {e}")
            return f"Error sending message: {str(e)}"


def track_lava_cost(user_id: str, model: str, estimated_tokens: int, operation: str) -> float:
    """
    Track AI processing costs per user via Lava

    Args:
        user_id: User identifier
        model: Model name (gpt-4o or gpt-4o-mini)
        estimated_tokens: Estimated token count
        operation: Operation type (OCR or categorization)

    Returns:
        Cost in dollars
    """
    # Lava cost per token (approximate based on model pricing)
    COST_PER_TOKEN = {
        "gpt-4o": 0.000005,      # $5 per 1M tokens (vision capable)
        "gpt-4o-mini": 0.00000015  # $0.15 per 1M tokens (text only)
    }

    cost = estimated_tokens * COST_PER_TOKEN.get(model, 0)

    # Initialize user cost tracking
    if user_id not in USER_COSTS:
        USER_COSTS[user_id] = {
            "total_cost": 0.0,
            "receipts_processed": 0,
            "history": []
        }

    # Update user costs
    USER_COSTS[user_id]["total_cost"] += cost
    USER_COSTS[user_id]["history"].append({
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "operation": operation,
        "tokens": estimated_tokens,
        "cost": cost
    })

    logger.info(f"💰 Lava Cost Tracking | User: {user_id} | {operation} ({model}) | Tokens: {estimated_tokens} | Cost: ${cost:.4f} | Total: ${USER_COSTS[user_id]['total_cost']:.4f}")

    return cost


def perform_ocr(image_url: str) -> Optional[str]:
    """
    Perform OCR on receipt image using GPT-4o vision capabilities

    Args:
        image_url: URL of the receipt image

    Returns:
        Extracted text or None if error
    """
    try:
        logger.info(f"Performing OCR on image: {image_url}")

        ocr_prompt = """
        You are an OCR system. Extract all text from this receipt image.
        Return the raw text exactly as it appears on the receipt, preserving line breaks.
        Include vendor name, date, items, amounts, and any other visible text.
        """

        message = HumanMessage(
            content=[
                {"type": "text", "text": ocr_prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        )

        response = ocr_llm.invoke([message])
        ocr_text = response.content.strip()

        logger.info(f"OCR completed. Extracted {len(ocr_text)} characters")
        return ocr_text

    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return None


def extract_expense_data(ocr_text: str, user_message: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract expense information from OCR text using LLM reasoning

    Args:
        ocr_text: Text extracted from receipt
        user_message: Optional user response to a clarification question

    Returns:
        Dictionary with 'status', and either 'data' (JSON) or 'question'
    """
    try:
        logger.info("Extracting expense data from OCR text")

        if user_message:
            # User is answering a clarification question
            prompt = f"""
            You are processing a receipt. Here is the text extracted from the receipt:

            {ocr_text}

            The user was asked for clarification and responded: "{user_message}"

            Now extract the following fields and return ONLY a valid JSON object with no additional text:
            {{
                "vendor": "business name",
                "amount": 0.00,
                "date": "YYYY-MM-DD",
                "category": "one of: food, travel, office_supplies, utilities, other",
                "expense_type": "business or personal"
            }}

            Use the user's response to fill in any missing information.
            If you still cannot determine a required field, use "unknown" for strings or 0.00 for amounts.
            Return ONLY the JSON object, no other text.
            """
        else:
            # First attempt at extraction
            prompt = f"""
            You are processing a receipt. Here is the text extracted from the receipt:

            {ocr_text}

            Extract the following expense information:
            - vendor: The business name
            - amount: The total amount (as a number)
            - date: The transaction date (in YYYY-MM-DD format)
            - category: One of: food, travel, office_supplies, utilities, other
            - expense_type: Either "business" or "personal"

            If you can extract ALL required fields with confidence, return ONLY a valid JSON object:
            {{
                "vendor": "business name",
                "amount": 0.00,
                "date": "YYYY-MM-DD",
                "category": "food",
                "expense_type": "business"
            }}

            If ANY required field is unclear or missing, return ONLY:
            QUESTION: <ask ONE specific clarifying question>

            For example:
            QUESTION: I can see the amount is $45.67, but what type of expense is this - business or personal?

            Return ONLY the JSON object OR the question line. No other text.
            """

        response = reasoning_llm.invoke([HumanMessage(content=prompt)])
        result_text = response.content.strip()

        logger.info(f"LLM response: {result_text[:200]}...")

        # Check if response is a question
        if result_text.startswith("QUESTION:"):
            question = result_text.replace("QUESTION:", "").strip()
            logger.info(f"LLM needs clarification: {question}")
            return {
                "status": "needs_clarification",
                "question": question
            }

        # Try to parse as JSON
        try:
            # Clean up any markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            data = json.loads(result_text)
            logger.info(f"Successfully extracted expense data: {data}")
            return {
                "status": "complete",
                "data": data
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.error(f"Response was: {result_text}")
            return {
                "status": "error",
                "error": "Failed to parse expense data"
            }

    except Exception as e:
        logger.error(f"Expense extraction failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool(description="Get AI processing cost analytics for a user - powered by Lava cost tracking")
def get_user_costs(user_id: str) -> str:
    """
    Return detailed cost analytics for a user's AI processing

    Args:
        user_id: User identifier

    Returns:
        JSON string with cost analytics powered by Lava
    """
    if user_id not in USER_COSTS:
        return json.dumps({
            "user_id": user_id,
            "total_ai_cost": 0.0,
            "receipts_processed": 0,
            "avg_cost_per_receipt": 0.0,
            "history": [],
            "powered_by": "Lava cost tracking",
            "message": "No receipts processed yet for this user"
        }, indent=2)

    user_data = USER_COSTS[user_id]
    receipts_count = user_data["receipts_processed"]
    total_cost = user_data["total_cost"]
    avg_cost = total_cost / max(1, receipts_count)

    return json.dumps({
        "user_id": user_id,
        "total_ai_cost": round(total_cost, 4),
        "receipts_processed": receipts_count,
        "avg_cost_per_receipt": round(avg_cost, 4),
        "recent_operations": user_data["history"][-5:],  # Last 5 operations
        "powered_by": "Lava cost tracking",
        "cost_breakdown": {
            "gpt_4o_vision": "Used for receipt OCR - $5/1M tokens",
            "gpt_4o_mini": "Used for categorization - $0.15/1M tokens (97% cheaper!)"
        }
    }, indent=2)


@mcp.tool(description="Process receipt images and text for expense tracking with conversational workflow")
def process_receipt(input_data: ReceiptInput) -> str:
    """
    Main tool for processing receipts with conversational workflow

    Handles three scenarios:
    1. New receipt image - performs OCR and attempts extraction
    2. User reply - finalizes extraction with user's answer
    3. Other messages - sends greeting

    Args:
        input_data: ReceiptInput containing user_id, message, and optional image_url

    Returns:
        JSON string with expense data or status message
    """
    user_id = input_data.user_id
    message = input_data.message
    image_url = input_data.image_url

    logger.info(f"Processing receipt for user {user_id}, has_image={bool(image_url)}, message_len={len(message)}")

    logger.info("Using direct processing")

    # Scenario 1: New receipt with image
    if image_url:
        logger.info(f"Scenario 1: Processing new receipt image for {user_id}")

        # Perform OCR
        ocr_text = perform_ocr(image_url)
        if not ocr_text:
            error_msg = "Sorry, I couldn't read the receipt image. Please try uploading a clearer photo."
            PokeReplyTool.send_message(user_id, error_msg)
            return json.dumps({"error": "OCR failed"})

        # Track Lava cost for OCR (GPT-4o vision)
        ocr_tokens = len(ocr_text) // 3  # Rough estimate: ~3 chars per token
        ocr_cost = track_lava_cost(user_id, "gpt-4o", ocr_tokens, "OCR")

        # Extract expense data
        extraction_result = extract_expense_data(ocr_text)

        # Track Lava cost for categorization (GPT-4o-mini)
        categorization_tokens = len(ocr_text) // 4  # Estimate
        categorization_cost = track_lava_cost(user_id, "gpt-4o-mini", categorization_tokens, "Categorization")

        if extraction_result["status"] == "complete":
            # All data extracted successfully
            data = extraction_result["data"]

            # Increment receipt counter
            USER_COSTS[user_id]["receipts_processed"] += 1

            # Add Lava cost data
            data["_lava_cost_data"] = {
                "this_receipt_cost": round(ocr_cost + categorization_cost, 4),
                "user_total_cost": round(USER_COSTS[user_id]["total_cost"], 4),
                "receipts_processed": USER_COSTS[user_id]["receipts_processed"],
                "cost_breakdown": {
                    "ocr_gpt4o": round(ocr_cost, 4),
                    "categorization_gpt4o_mini": round(categorization_cost, 4)
                }
            }

            success_msg = f"✅ Receipt processed!\n\nVendor: {data['vendor']}\nAmount: ${data['amount']}\nCategory: {data['category']}\n\n💰 Cost: ${data['_lava_cost_data']['this_receipt_cost']} (via Lava)"
            PokeReplyTool.send_message(user_id, success_msg)

            return json.dumps(data, indent=2)

        elif extraction_result["status"] == "needs_clarification":
            # Need to ask user a question
            question = extraction_result["question"]

            # Save state
            USER_STATES[user_id] = {
                "status": "awaiting_reply",
                "ocr_text": ocr_text,
                "timestamp": datetime.now().isoformat()
            }

            # Send question to user
            PokeReplyTool.send_message(user_id, question)
            return json.dumps({
                "status": "awaiting_user_reply",
                "question": question
            })

        else:
            # Error occurred
            error_msg = f"Sorry, I encountered an error processing the receipt: {extraction_result.get('error', 'Unknown error')}"
            PokeReplyTool.send_message(user_id, error_msg)
            return json.dumps(extraction_result)

    # Scenario 2: User reply to clarification question
    elif user_id in USER_STATES and USER_STATES[user_id].get("status") == "awaiting_reply":
        logger.info(f"Scenario 2: Processing user reply for {user_id}")

        # Retrieve state
        state = USER_STATES[user_id]
        ocr_text = state["ocr_text"]

        # Finalize extraction with user's answer
        extraction_result = extract_expense_data(ocr_text, user_message=message)

        # Clear state
        del USER_STATES[user_id]

        if extraction_result["status"] == "complete":
            data = extraction_result["data"]

            # Send final result to user
            success_msg = f"Got it! Receipt saved:\n\nVendor: {data['vendor']}\nAmount: ${data['amount']}\nDate: {data['date']}\nCategory: {data['category']}\nType: {data['expense_type']}"
            PokeReplyTool.send_message(user_id, success_msg)

            return json.dumps(data, indent=2)
        else:
            error_msg = f"Sorry, I had trouble finalizing the receipt: {extraction_result.get('error', 'Unknown error')}"
            PokeReplyTool.send_message(user_id, error_msg)
            return json.dumps(extraction_result)

    # Scenario 3: Other messages (greeting, random text, etc.)
    else:
        logger.info(f"Scenario 3: Default greeting for {user_id}")
        greeting = "Hi! I'm your Conversational CFO. Send me a receipt image and I'll help you track the expense."
        PokeReplyTool.send_message(user_id, greeting)
        return json.dumps({"status": "greeting_sent", "message": greeting})


# Poke Webhook Handler (for bidirectional integration)
# NOTE: Commented out for demo - FastMCP doesn't directly expose .app.post()
# For production, this would be implemented via custom FastAPI routes
#
# @mcp.app.post("/webhook/poke")
# async def poke_webhook_handler(request):
#     """
#     Handle incoming messages from Poke
#     Makes the integration bidirectional - receive messages from Poke!
#
#     Expected Poke webhook format:
#     {
#       "user_id": "string",
#       "message": "string",
#       "attachments": [{"type": "image", "url": "string"}]
#     }
#     """
#     try:
#         from fastapi import Request
#
#         data = await request.json()
#         logger.info(f"📱 Poke Webhook: Received message from {data.get('user_id')}")
#
#         user_id = data.get("user_id", "unknown")
#         message = data.get("message", "")
#         attachments = data.get("attachments", [])
#
#         # Extract image URL from attachments
#         image_url = None
#         for attachment in attachments:
#             if attachment.get("type") == "image":
#                 image_url = attachment.get("url")
#                 break
#
#         # Process via MCP tool
#         result = process_receipt(ReceiptInput(
#             user_id=user_id,
#             message=message,
#             image_url=image_url
#         ))
#
#         logger.info(f"✅ Poke Webhook: Processed message for {user_id}")
#
#         return {
#             "status": "success",
#             "message": "Receipt processed via Poke webhook",
#             "result": result
#         }
#
#     except Exception as e:
#         logger.error(f"❌ Poke Webhook error: {e}")
#         return {
#             "status": "error",
#             "message": str(e)
#         }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"

    logger.info("="*70)
    logger.info("🚀 CONVERSATIONAL CFO MCP SERVER")
    logger.info("="*70)
    logger.info(f"Server: {host}:{port}")
    logger.info(f"Lava Proxy: {LAVA_BASE_URL}")
    logger.info(f"OCR Model: gpt-4o (via Lava)")
    logger.info(f"Reasoning Model: gpt-4o-mini (via Lava)")
    logger.info("="*70)

    logger.info("✅ Server starting...")
    logger.info("")

    mcp.run(
        transport="http",
        host=host,
        port=port,
        stateless_http=True
    )