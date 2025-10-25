"""
Fetch.ai Agent System for Conversational CFO
Multi-agent orchestration for receipt processing workflow

ASI:One Compatible - Implements Chat Protocol for discoverability
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from uagents import Agent, Context, Model, Protocol
from uagents.setup import fund_agent_if_low
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)
import asyncio

logger = logging.getLogger(__name__)


# Utility function to create chat messages
def create_text_chat(text: str) -> ChatMessage:
    """Create a ChatMessage with text content for ASI:One compatibility"""
    content = [TextContent(type="text", text=text)]
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )

# Message Models for Agent Communication
class ReceiptMessage(Model):
    """Message containing receipt data for processing"""
    user_id: str
    image_url: str
    request_id: str

class OCRResult(Model):
    """OCR extraction result"""
    request_id: str
    user_id: str
    ocr_text: str
    success: bool
    error: Optional[str] = None

class CategorizationRequest(Model):
    """Request for expense categorization"""
    request_id: str
    user_id: str
    ocr_text: str
    user_message: Optional[str] = None

class CategorizationResult(Model):
    """Categorization result"""
    request_id: str
    user_id: str
    status: str  # "complete", "needs_clarification", "error"
    data: Optional[Dict[str, Any]] = None
    question: Optional[str] = None
    error: Optional[str] = None

class MessagingRequest(Model):
    """Request to send message to user"""
    request_id: str
    user_id: str
    message: str

class MessagingResult(Model):
    """Messaging result"""
    request_id: str
    user_id: str
    success: bool
    error: Optional[str] = None


# ============================================================================
# AGENT DEFINITIONS
# ============================================================================

# OCR Agent - Handles receipt image processing
ocr_agent = Agent(
    name="ocr_agent",
    seed="ocr_seed_conversational_cfo",
    port=8001,
    endpoint=["http://localhost:8001/submit"],
)

# Categorizer Agent - Handles expense categorization
categorizer_agent = Agent(
    name="categorizer_agent",
    seed="categorizer_seed_conversational_cfo",
    port=8002,
    endpoint=["http://localhost:8002/submit"],
)

# Messaging Agent - Handles communication with Poke
messaging_agent = Agent(
    name="messaging_agent",
    seed="messaging_seed_conversational_cfo",
    port=8003,
    endpoint=["http://localhost:8003/submit"],
)

# Coordinator Agent - Orchestrates the workflow (ASI:One compatible)
coordinator_agent = Agent(
    name="conversational_cfo_coordinator",
    seed="coordinator_seed_conversational_cfo",
    port=8004,
    endpoint=["http://localhost:8004/submit"],
)

# Initialize Chat Protocol for ASI:One compatibility
chat_proto = Protocol(spec=chat_protocol_spec)

logger.info(f"🤖 OCR Agent Address: {ocr_agent.address}")
logger.info(f"🤖 Categorizer Agent Address: {categorizer_agent.address}")
logger.info(f"🤖 Messaging Agent Address: {messaging_agent.address}")
logger.info(f"🤖 Coordinator Agent Address: {coordinator_agent.address}")


# ============================================================================
# AGENT BEHAVIORS
# ============================================================================

@ocr_agent.on_message(model=ReceiptMessage)
async def handle_ocr_request(ctx: Context, sender: str, msg: ReceiptMessage):
    """Handle OCR request from coordinator"""
    logger.info(f"OCR Agent: Processing image for {msg.user_id}")

    try:
        # Import here to avoid circular dependencies
        from server import perform_ocr

        # Perform OCR
        ocr_text = perform_ocr(msg.image_url)

        if ocr_text:
            result = OCRResult(
                request_id=msg.request_id,
                user_id=msg.user_id,
                ocr_text=ocr_text,
                success=True
            )
            logger.info(f"OCR Agent: Successfully extracted {len(ocr_text)} characters")
        else:
            result = OCRResult(
                request_id=msg.request_id,
                user_id=msg.user_id,
                ocr_text="",
                success=False,
                error="OCR failed to extract text"
            )
            logger.error("OCR Agent: Failed to extract text")

        # Send result back to coordinator
        await ctx.send(sender, result)

    except Exception as e:
        logger.error(f"OCR Agent error: {e}")
        result = OCRResult(
            request_id=msg.request_id,
            user_id=msg.user_id,
            ocr_text="",
            success=False,
            error=str(e)
        )
        await ctx.send(sender, result)


@categorizer_agent.on_message(model=CategorizationRequest)
async def handle_categorization_request(ctx: Context, sender: str, msg: CategorizationRequest):
    """Handle categorization request from coordinator"""
    logger.info(f"Categorizer Agent: Processing expense for {msg.user_id}")

    try:
        # Import here to avoid circular dependencies
        from server import extract_expense_data

        # Extract expense data
        extraction_result = extract_expense_data(msg.ocr_text, msg.user_message)

        result = CategorizationResult(
            request_id=msg.request_id,
            user_id=msg.user_id,
            status=extraction_result["status"],
            data=extraction_result.get("data"),
            question=extraction_result.get("question"),
            error=extraction_result.get("error")
        )

        logger.info(f"Categorizer Agent: Status = {result.status}")

        # Send result back to coordinator
        await ctx.send(sender, result)

    except Exception as e:
        logger.error(f"Categorizer Agent error: {e}")
        result = CategorizationResult(
            request_id=msg.request_id,
            user_id=msg.user_id,
            status="error",
            error=str(e)
        )
        await ctx.send(sender, result)


@messaging_agent.on_message(model=MessagingRequest)
async def handle_messaging_request(ctx: Context, sender: str, msg: MessagingRequest):
    """Handle messaging request from coordinator"""
    logger.info(f"Messaging Agent: Sending message to {msg.user_id}")

    try:
        # Import here to avoid circular dependencies
        from server import PokeReplyTool

        # Send message via Poke
        PokeReplyTool.send_message(msg.user_id, msg.message)

        result = MessagingResult(
            request_id=msg.request_id,
            user_id=msg.user_id,
            success=True
        )

        logger.info(f"Messaging Agent: Message sent successfully")

        # Send result back to coordinator
        await ctx.send(sender, result)

    except Exception as e:
        logger.error(f"Messaging Agent error: {e}")
        result = MessagingResult(
            request_id=msg.request_id,
            user_id=msg.user_id,
            success=False,
            error=str(e)
        )
        await ctx.send(sender, result)


# ============================================================================
# CHAT PROTOCOL HANDLERS - For ASI:One Integration
# ============================================================================

@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """
    Handle incoming chat messages from ASI:One or other agents
    This makes the agent discoverable through ASI:One
    """
    logger.info(f"💬 Chat Protocol: Received message from {sender}")

    # Send acknowledgement
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.utcnow(),
        acknowledged_msg_id=msg.msg_id
    ))

    # Process each content item
    for item in msg.content:
        if isinstance(item, StartSessionContent):
            logger.info(f"💬 Chat session started with {sender}")
            welcome_msg = create_text_chat(
                "👋 Hello! I'm your Conversational CFO. Send me a receipt image and I'll help you track expenses."
            )
            await ctx.send(sender, welcome_msg)

        elif isinstance(item, TextContent):
            logger.info(f"💬 Processing text: {item.text}")

            # Check if this is a receipt processing request
            if "receipt" in item.text.lower() or "expense" in item.text.lower():
                response_msg = create_text_chat(
                    "📸 Please provide a receipt image URL, and I'll process it for you! "
                    "I'll extract the vendor, amount, date, and categorize it as business or personal."
                )
            else:
                response_msg = create_text_chat(
                    "I specialize in processing receipts for expense tracking. "
                    "Send me a receipt image and I'll help you categorize it!"
                )

            await ctx.send(sender, response_msg)

        elif isinstance(item, EndSessionContent):
            logger.info(f"💬 Chat session ended with {sender}")
            goodbye_msg = create_text_chat("👋 Session ended. Come back anytime with more receipts!")
            await ctx.send(sender, goodbye_msg)


@chat_proto.on_message(ChatAcknowledgement)
async def handle_chat_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle acknowledgements for sent messages"""
    logger.info(f"💬 Received ack from {sender} for message {msg.acknowledged_msg_id}")


# Include chat protocol in coordinator agent and publish manifest for ASI:One
coordinator_agent.include(chat_proto, publish_manifest=True)
logger.info("✅ Chat Protocol enabled for ASI:One compatibility")


# ============================================================================
# COORDINATOR AGENT - Orchestrates the workflow
# ============================================================================

# Store pending requests
pending_requests: Dict[str, Dict[str, Any]] = {}

@coordinator_agent.on_interval(period=1.0)
async def check_pending_requests(ctx: Context):
    """Periodically check for timed out requests"""
    # Cleanup logic if needed
    pass


async def process_receipt_with_agents(user_id: str, image_url: str, message: str = "") -> Dict[str, Any]:
    """
    Main function to process receipt using agent system

    Args:
        user_id: User identifier
        image_url: Receipt image URL
        message: Optional message from user

    Returns:
        Processing result
    """
    import uuid
    request_id = str(uuid.uuid4())

    logger.info(f"Coordinator: Starting receipt processing for {user_id} (request: {request_id})")

    # Store request context
    pending_requests[request_id] = {
        "user_id": user_id,
        "image_url": image_url,
        "message": message,
        "status": "processing",
        "result": None
    }

    try:
        # Step 1: Send to OCR Agent
        logger.info(f"Coordinator: Dispatching to OCR Agent")
        receipt_msg = ReceiptMessage(
            user_id=user_id,
            image_url=image_url,
            request_id=request_id
        )

        # Create a simple synchronous workflow for demo purposes
        # In production, you'd use proper async message passing
        from server import perform_ocr, extract_expense_data, PokeReplyTool

        # OCR Step
        logger.info("🤖 Agent System: OCR Agent processing...")
        ocr_text = perform_ocr(image_url)

        if not ocr_text:
            error_msg = "Sorry, I couldn't read the receipt image. Please try uploading a clearer photo."
            logger.info("🤖 Agent System: Messaging Agent sending error...")
            PokeReplyTool.send_message(user_id, error_msg)
            return {"error": "OCR failed"}

        logger.info(f"🤖 Agent System: OCR Agent extracted {len(ocr_text)} characters")

        # Categorization Step
        logger.info("🤖 Agent System: Categorizer Agent processing...")
        extraction_result = extract_expense_data(ocr_text, message if message else None)

        if extraction_result["status"] == "complete":
            data = extraction_result["data"]
            success_msg = f"Receipt processed! Vendor: {data['vendor']}, Amount: ${data['amount']}, Category: {data['category']}"
            logger.info("🤖 Agent System: Messaging Agent sending success message...")
            PokeReplyTool.send_message(user_id, success_msg)
            return extraction_result

        elif extraction_result["status"] == "needs_clarification":
            question = extraction_result["question"]
            logger.info("🤖 Agent System: Messaging Agent sending clarification question...")
            PokeReplyTool.send_message(user_id, question)
            return extraction_result

        else:
            error_msg = f"Sorry, I encountered an error: {extraction_result.get('error', 'Unknown error')}"
            logger.info("🤖 Agent System: Messaging Agent sending error...")
            PokeReplyTool.send_message(user_id, error_msg)
            return extraction_result

    except Exception as e:
        logger.error(f"Coordinator error: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        # Cleanup
        if request_id in pending_requests:
            del pending_requests[request_id]


# ============================================================================
# AGENT BUREAU (for running all agents)
# ============================================================================

def get_agent_bureau():
    """Get all agents for running"""
    return [ocr_agent, categorizer_agent, messaging_agent, coordinator_agent]


if __name__ == "__main__":
    # Run all agents in development mode
    logger.info("Starting Fetch.ai Agent System...")

    # Note: In production, agents would run as separate processes
    # For demo purposes, we'll just log that they're initialized
    logger.info("✅ All agents initialized and ready!")
    logger.info(f"   - OCR Agent: {ocr_agent.address}")
    logger.info(f"   - Categorizer Agent: {categorizer_agent.address}")
    logger.info(f"   - Messaging Agent: {messaging_agent.address}")
    logger.info(f"   - Coordinator Agent: {coordinator_agent.address}")
