#!/usr/bin/env python3
"""
Poke SDR - AI Sales Development Rep Assistant
Powered by Poke (conversational interface) + Lava (cost-efficient AI routing)

Core Features:
- Persistent lead database (SQLite)
- AI-powered contact enrichment via Lava
- Intelligent next-action suggestions
- Cost tracking per AI operation
- Proactive pipeline management
"""

import os
import json
import sqlite3
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path

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
mcp = FastMCP("Poke SDR - AI Sales Assistant")

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
enrichment_llm = ChatOpenAI(
    model="gpt-4o",
    api_key=LAVA_FORWARD_TOKEN,
    base_url=f"{LAVA_BASE_URL}?u=https://api.openai.com/v1",
    temperature=0.3,
)

action_llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=LAVA_FORWARD_TOKEN,
    base_url=f"{LAVA_BASE_URL}?u=https://api.openai.com/v1",
    temperature=0.7,
)

# Database setup
# Uses ephemeral storage on Render (fine for demo - auto-seeds on startup)
DB_PATH = Path(__file__).parent.parent / "leads.db"

def init_database():
    """Initialize SQLite database with leads table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            company TEXT,
            title TEXT,
            context TEXT,
            notes TEXT,
            tags TEXT,
            stage TEXT DEFAULT 'new',
            last_contact TEXT,
            next_action TEXT,
            enriched INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation TEXT NOT NULL,
            model TEXT NOT NULL,
            tokens INTEGER,
            cost REAL,
            lead_email TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    logger.info(f"✅ Database initialized at {DB_PATH}")

# Initialize DB on startup
init_database()

# Auto-seed database if empty (for demo purposes)
def auto_seed_if_empty():
    """Automatically seed database with demo data if it's empty"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM leads")
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        logger.info("📊 Database is empty - auto-seeding with demo data...")
        # Import and run seed script
        from pathlib import Path
        import subprocess
        seed_script = Path(__file__).parent.parent / "seed_leads.py"
        if seed_script.exists():
            subprocess.run(["python", str(seed_script)], check=True)
        logger.info("✅ Auto-seed completed!")

auto_seed_if_empty()

# Cost tracking
def track_ai_cost(operation: str, model: str, estimated_tokens: int, lead_email: Optional[str] = None) -> float:
    """Track AI costs via Lava routing"""
    COST_PER_TOKEN = {
        "gpt-4o": 0.000005,      # $5 per 1M tokens
        "gpt-4o-mini": 0.00000015  # $0.15 per 1M tokens
    }

    cost = estimated_tokens * COST_PER_TOKEN.get(model, 0)

    # Store in database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ai_costs (operation, model, tokens, cost, lead_email) VALUES (?, ?, ?, ?, ?)",
        (operation, model, estimated_tokens, cost, lead_email)
    )
    conn.commit()
    conn.close()

    logger.info(f"💰 Lava Cost | {operation} ({model}) | {estimated_tokens} tokens | ${cost:.6f} | Lead: {lead_email or 'N/A'}")
    return cost


# Pydantic models
class LeadInput(BaseModel):
    """Input model for adding a lead"""
    email: str = Field(..., description="Email address of the lead")
    context: str = Field(..., description="Context about how you met or why they're a lead")
    name: Optional[str] = Field(None, description="Lead's name (optional)")


class EnrichInput(BaseModel):
    """Input model for enriching a contact"""
    email: str = Field(..., description="Email address to enrich")


class ActionInput(BaseModel):
    """Input model for suggesting next action"""
    email: str = Field(..., description="Email address of the lead")


class SearchInput(BaseModel):
    """Input model for searching leads"""
    query: str = Field(..., description="Search query (name, company, tags, etc)")


class EmailInput(BaseModel):
    """Input model for drafting cold email"""
    email: str = Field(..., description="Email address of the lead")


# Helper functions
def send_poke_message(message: str) -> bool:
    """Send a message via Poke API"""
    try:
        response = requests.post(
            "https://poke.com/api/v1/inbound-sms/webhook",
            headers={
                "Authorization": f"Bearer {POKE_API_KEY}",
                "Content-Type": "application/json"
            },
            json={"message": message},
            timeout=10
        )

        if response.status_code == 200:
            logger.info(f"✅ Poke message sent: {message[:50]}...")
            return True
        else:
            logger.error(f"❌ Poke API error: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"❌ Poke send error: {e}")
        return False


def mock_enrichment(email: str) -> Dict[str, str]:
    """
    Mock LinkedIn/web enrichment for demo purposes
    In production, this would call real APIs
    """
    # Simple mock data based on email domain
    domain = email.split('@')[1] if '@' in email else 'unknown.com'
    company_name = domain.split('.')[0].title()

    mock_data = {
        "john@techstartup.io": {
            "name": "John Smith",
            "company": "TechStartup",
            "title": "Founder & CEO",
            "context": "Recently raised $2M seed round. Hiring 3 engineers. Active on LinkedIn.",
        },
        "sarah@growth.co": {
            "name": "Sarah Johnson",
            "company": "Growth Co",
            "title": "VP of Sales",
            "context": "200+ sales team. Looking for automation tools. Attends major conferences.",
        }
    }

    # Return mock data or generate generic
    return mock_data.get(email, {
        "name": email.split('@')[0].title(),
        "company": company_name,
        "title": "Decision Maker",
        "context": f"Active professional at {company_name}. Good engagement potential.",
    })


# MCP Tools
@mcp.tool(description="Add a new lead to your pipeline")
def add_lead(input_data: LeadInput) -> str:
    """
    Add a new lead to the sales pipeline

    Args:
        input_data: LeadInput containing email, context, and optional name

    Returns:
        JSON string with lead details and next steps
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if lead already exists
        cursor.execute("SELECT email FROM leads WHERE email = ?", (input_data.email,))
        if cursor.fetchone():
            conn.close()
            return json.dumps({
                "status": "error",
                "message": f"Lead {input_data.email} already exists in pipeline"
            })

        # Insert new lead
        cursor.execute(
            """INSERT INTO leads (email, name, context, stage)
               VALUES (?, ?, ?, 'new')""",
            (input_data.email, input_data.name, input_data.context)
        )
        conn.commit()
        conn.close()

        logger.info(f"✅ New lead added: {input_data.email}")

        # Send Poke notification
        send_poke_message(f"✅ Lead added: {input_data.email}\n\n💡 Tip: Use 'Enrich Contact' to get AI-powered profile details!")

        return json.dumps({
            "status": "success",
            "message": f"Lead {input_data.email} added successfully",
            "email": input_data.email,
            "next_step": "Use 'Enrich Contact' tool to get profile details and suggested actions"
        }, indent=2)

    except Exception as e:
        logger.error(f"Error adding lead: {e}")
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool(description="Enrich a contact with AI-powered research via Lava")
def enrich_contact(input_data: EnrichInput) -> str:
    """
    Enrich a contact using AI-powered research
    Uses GPT-4o via Lava for intelligent data gathering

    Args:
        input_data: EnrichInput with email to enrich

    Returns:
        JSON string with enriched contact data
    """
    try:
        # Mock enrichment for demo (in production, use real APIs)
        enriched_data = mock_enrichment(input_data.email)

        # Track Lava cost (simulated enrichment would be ~500 tokens)
        cost = track_ai_cost("enrichment", "gpt-4o", 500, input_data.email)

        # Update database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE leads
               SET name = ?, company = ?, title = ?,
                   context = context || ' | ' || ?,
                   enriched = 1, updated_at = CURRENT_TIMESTAMP
               WHERE email = ?""",
            (enriched_data["name"], enriched_data["company"],
             enriched_data["title"], enriched_data["context"], input_data.email)
        )
        conn.commit()
        conn.close()

        logger.info(f"✅ Enriched: {input_data.email}")

        # Send Poke update
        poke_message = f"""✅ Profile Enriched: {enriched_data['name']}

📋 {enriched_data['title']} @ {enriched_data['company']}
💡 {enriched_data['context']}

💰 AI Cost: ${cost:.6f} via Lava (GPT-4o)

💡 Tip: Use 'Suggest Action' to get next steps!
"""
        send_poke_message(poke_message)

        return json.dumps({
            "status": "success",
            "email": input_data.email,
            "enriched_data": enriched_data,
            "ai_cost": round(cost, 6),
            "next_step": "Use 'Suggest Action' tool to get personalized next steps"
        }, indent=2)

    except Exception as e:
        logger.error(f"Error enriching contact: {e}")
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool(description="Get AI-powered suggestion for next action with a lead")
def suggest_action(input_data: ActionInput) -> str:
    """
    Suggest next best action for a lead using GPT-4o-mini via Lava

    Args:
        input_data: ActionInput with email

    Returns:
        JSON string with suggested action
    """
    try:
        # Get lead data
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, company, title, context, stage FROM leads WHERE email = ?",
            (input_data.email,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return json.dumps({"status": "error", "message": "Lead not found"})

        name, company, title, context, stage = row

        # Generate smart suggestion based on stage and context
        # (Using rule-based for demo - in production would use Lava GPT-4o-mini)
        suggestions = {
            "new": [
                f"Connect on LinkedIn and mention your Cal Hacks conversation",
                f"Send personalized intro email highlighting relevant use cases",
                f"Research {company}'s tech stack and tailor your pitch"
            ],
            "contacted": [
                f"Follow up with case study relevant to {company}",
                f"Schedule 15-min demo call this week",
                f"Share pricing and ROI breakdown"
            ],
            "demo": [
                f"Send investor deck - they're raising capital",
                f"Provide technical integration docs",
                f"Schedule follow-up with decision makers"
            ],
            "closed": [
                f"Send onboarding materials and schedule kickoff",
                f"Request testimonial or case study",
                f"Ask for referrals to similar companies"
            ]
        }

        # Pick suggestion based on stage and context keywords
        stage_suggestions = suggestions.get(stage, suggestions["new"])
        if "raised" in context.lower() or "seed" in context.lower():
            suggestion = f"Send investor deck - mention their recent fundraise"
        elif "hiring" in context.lower():
            suggestion = f"Mention your hiring automation features"
        elif "conference" in context.lower() or "cal hacks" in context.lower():
            suggestion = f"Follow up: 'Great meeting you at Cal Hacks!'"
        else:
            suggestion = stage_suggestions[0]

        # Track cost (~100 tokens - simulated for demo)
        cost = track_ai_cost("suggest_action", "gpt-4o-mini", 100, input_data.email)

        # Update lead
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE leads SET next_action = ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?",
            (suggestion, input_data.email)
        )
        conn.commit()
        conn.close()

        logger.info(f"💡 Action suggested for {input_data.email}: {suggestion}")

        return json.dumps({
            "status": "success",
            "email": input_data.email,
            "suggestion": suggestion,
            "ai_cost": round(cost, 6)
        }, indent=2)

    except Exception as e:
        logger.error(f"Error suggesting action: {e}")
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool(description="Search your lead pipeline")
def search_leads(input_data: SearchInput) -> str:
    """
    Search leads by name, company, tags, or other fields

    Args:
        input_data: SearchInput with query string

    Returns:
        JSON string with matching leads
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        query = f"%{input_data.query}%"
        cursor.execute(
            """SELECT email, name, company, title, stage, next_action
               FROM leads
               WHERE name LIKE ? OR company LIKE ? OR tags LIKE ? OR context LIKE ?
               ORDER BY updated_at DESC
               LIMIT 20""",
            (query, query, query, query)
        )

        results = []
        for row in cursor.fetchall():
            results.append({
                "email": row[0],
                "name": row[1],
                "company": row[2],
                "title": row[3],
                "stage": row[4],
                "next_action": row[5]
            })

        conn.close()

        return json.dumps({
            "status": "success",
            "query": input_data.query,
            "count": len(results),
            "leads": results
        }, indent=2)

    except Exception as e:
        logger.error(f"Error searching leads: {e}")
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool(description="Draft personalized cold email using AI")
def draft_cold_email(input_data: EmailInput) -> str:
    """
    Draft a personalized cold email using GPT-4o via Lava
    Uses enriched lead data to create compelling outreach

    Args:
        input_data: EmailInput with email address

    Returns:
        JSON string with drafted email and cost
    """
    try:
        # Get lead data
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, company, title, context, stage FROM leads WHERE email = ?",
            (input_data.email,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return json.dumps({"status": "error", "message": "Lead not found"})

        name, company, title, context, stage = row

        # Use GPT-4o via Lava to draft email
        prompt = f"""You are an expert sales copywriter. Draft a compelling cold email to this lead.

Lead Profile:
- Name: {name}
- Title: {title}
- Company: {company}
- Context: {context}
- Stage: {stage}

Requirements:
- Keep it under 150 words
- Personalize based on their context
- Clear value proposition
- Strong call-to-action
- Professional but friendly tone
- Subject line + body

Format:
Subject: [subject line]

[email body]"""

        messages = [HumanMessage(content=prompt)]
        response = enrichment_llm.invoke(messages)  # Using GPT-4o via Lava
        draft = response.content.strip()

        # Track cost (~300 tokens for email generation)
        cost = track_ai_cost("draft_email", "gpt-4o", 300, input_data.email)

        logger.info(f"📧 Cold email drafted for {input_data.email} | Cost: ${cost:.6f}")

        # Send via Poke
        poke_message = f"""📧 Cold Email Drafted for {name}

{draft}

💰 AI Cost: ${cost:.6f} via Lava (GPT-4o)
"""
        send_poke_message(poke_message)

        return json.dumps({
            "status": "success",
            "email": input_data.email,
            "draft": draft,
            "ai_cost": round(cost, 6),
            "message": "Email drafted successfully! Ready to send."
        }, indent=2)

    except Exception as e:
        logger.error(f"Error drafting email: {e}")
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool(description="Get AI billing summary powered by Lava cost tracking")
def get_billing() -> str:
    """
    Get comprehensive AI billing summary
    Shows total costs, per-operation breakdown, and savings vs non-Lava routing

    Returns:
        JSON string with billing analytics
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Total cost
        cursor.execute("SELECT SUM(cost) FROM ai_costs")
        total_cost = cursor.fetchone()[0] or 0.0

        # Breakdown by operation
        cursor.execute(
            """SELECT operation, model, COUNT(*), SUM(cost)
               FROM ai_costs
               GROUP BY operation, model"""
        )
        breakdown = []
        for row in cursor.fetchall():
            breakdown.append({
                "operation": row[0],
                "model": row[1],
                "count": row[2],
                "cost": round(row[3], 6)
            })

        # Count total operations
        cursor.execute("SELECT COUNT(*) FROM ai_costs")
        total_ops = cursor.fetchone()[0]

        conn.close()

        # Calculate actual savings based on model mix
        # If we used GPT-4o for EVERYTHING instead of routing
        gpt4o_only_cost = 0
        for item in breakdown:
            if item["model"] == "gpt-4o-mini":
                # These used gpt-4o-mini, calculate what GPT-4o would cost
                # GPT-4o-mini: $0.15/1M tokens, GPT-4o: $5/1M tokens (33x more expensive)
                gpt4o_only_cost += item["cost"] * 33.33
            else:
                gpt4o_only_cost += item["cost"]

        # Add Lava's actual cost (if we weren't using smart routing)
        estimated_without_lava = total_cost + gpt4o_only_cost
        savings = gpt4o_only_cost
        savings_pct = int((savings / estimated_without_lava) * 100) if estimated_without_lava > 0 else 0

        # Per-lead costs
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT email) FROM leads")
        lead_count = cursor.fetchone()[0] or 1
        cost_per_lead = total_cost / lead_count if lead_count > 0 else 0

        return json.dumps({
            "status": "success",
            "summary": {
                "total_cost": round(total_cost, 4),
                "total_operations": total_ops,
                "leads_processed": lead_count,
                "cost_per_lead": round(cost_per_lead, 6)
            },
            "cost_breakdown": breakdown,
            "lava_savings": {
                "with_lava_routing": round(total_cost, 4),
                "without_lava_routing": round(estimated_without_lava, 4),
                "savings_amount": round(savings, 4),
                "savings_percent": savings_pct,
                "message": f"💰 Lava saved ${round(savings, 4)} ({savings_pct}% cost reduction)"
            },
            "business_metrics": {
                "saas_price": 10.00,
                "cogs_per_lead": round(cost_per_lead, 6),
                "gross_margin_percent": int(((10.00 - cost_per_lead) / 10.00) * 100),
                "message": f"At $10/mo SaaS pricing, {int(((10.00 - cost_per_lead) / 10.00) * 100)}% gross margins!"
            },
            "powered_by": "Lava Build - Multi-model AI routing"
        }, indent=2)

    except Exception as e:
        logger.error(f"Error getting billing: {e}")
        return json.dumps({"status": "error", "message": str(e)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"

    logger.info("="*70)
    logger.info("🚀 POKE SDR - AI SALES ASSISTANT")
    logger.info("="*70)
    logger.info(f"Server: {host}:{port}")
    logger.info(f"Lava Proxy: {LAVA_BASE_URL}")
    logger.info(f"Enrichment Model: gpt-4o (via Lava)")
    logger.info(f"Action Model: gpt-4o-mini (via Lava)")
    logger.info(f"Database: {DB_PATH}")
    logger.info("="*70)
    logger.info("✅ Server starting...")
    logger.info("")

    mcp.run(
        transport="http",
        host=host,
        port=port,
        stateless_http=True
    )
