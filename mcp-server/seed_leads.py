#!/usr/bin/env python3
"""Seed the database with sample leads for demo purposes"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "leads.db"

# Sample leads matching the dashboard
leads = [
    {
        "email": "john@techstartup.io",
        "name": "John Smith",
        "company": "TechStartup",
        "title": "Founder & CEO",
        "context": "Met at Cal Hacks booth. Recently raised $2M seed round. Hiring 3 engineers. Active on LinkedIn.",
        "stage": "demo",
        "next_action": "Send investor deck - they just raised $2M seed",
        "enriched": 1
    },
    {
        "email": "sarah@growth.co",
        "name": "Sarah Johnson",
        "company": "Growth Co",
        "title": "VP of Sales",
        "context": "200+ sales team. Looking for automation tools. Attends major conferences.",
        "stage": "contacted",
        "next_action": "Follow up about automation tools demo",
        "enriched": 1
    },
    {
        "email": "mike@enterprise.com",
        "name": "Mike Chen",
        "company": "Enterprise Corp",
        "title": "CTO",
        "context": "Active professional at Enterprise Corp. Good engagement potential.",
        "stage": "new",
        "next_action": "Research their tech stack, mention AI integration",
        "enriched": 1
    },
    {
        "email": "emily@startup.ai",
        "name": "Emily Davis",
        "company": "Startup AI",
        "title": "Product Manager",
        "context": "AI-focused startup. Looking for workflow tools.",
        "stage": "contacted",
        "next_action": "Send case study on workflow automation",
        "enriched": 1
    },
    {
        "email": "alex@innovate.tech",
        "name": "Alex Martinez",
        "company": "Innovate Tech",
        "title": "Engineering Lead",
        "context": "Met at Cal Hacks. Interested in developer tools.",
        "stage": "new",
        "next_action": "Connect on LinkedIn, mention Cal Hacks",
        "enriched": 1
    }
]

# Sample AI costs
costs = [
    {"operation": "enrichment", "model": "gpt-4o", "tokens": 500, "cost": 0.0025, "lead_email": "john@techstartup.io"},
    {"operation": "suggest_action", "model": "gpt-4o-mini", "tokens": 100, "cost": 0.000015, "lead_email": "john@techstartup.io"},
    {"operation": "enrichment", "model": "gpt-4o", "tokens": 500, "cost": 0.0025, "lead_email": "sarah@growth.co"},
    {"operation": "suggest_action", "model": "gpt-4o-mini", "tokens": 100, "cost": 0.000015, "lead_email": "sarah@growth.co"},
    {"operation": "enrichment", "model": "gpt-4o", "tokens": 500, "cost": 0.0025, "lead_email": "mike@enterprise.com"},
    {"operation": "suggest_action", "model": "gpt-4o-mini", "tokens": 100, "cost": 0.000015, "lead_email": "mike@enterprise.com"},
    {"operation": "enrichment", "model": "gpt-4o", "tokens": 500, "cost": 0.0025, "lead_email": "emily@startup.ai"},
    {"operation": "suggest_action", "model": "gpt-4o-mini", "tokens": 100, "cost": 0.000015, "lead_email": "emily@startup.ai"},
    {"operation": "enrichment", "model": "gpt-4o", "tokens": 500, "cost": 0.0025, "lead_email": "alex@innovate.tech"},
    {"operation": "suggest_action", "model": "gpt-4o-mini", "tokens": 100, "cost": 0.000015, "lead_email": "alex@innovate.tech"},
]

def seed_database():
    """Seed the database with sample data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute("DELETE FROM leads")
    cursor.execute("DELETE FROM ai_costs")

    # Insert leads
    for lead in leads:
        cursor.execute(
            """INSERT INTO leads (email, name, company, title, context, stage, next_action, enriched)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (lead["email"], lead["name"], lead["company"], lead["title"],
             lead["context"], lead["stage"], lead["next_action"], lead["enriched"])
        )

    # Insert costs
    for cost in costs:
        cursor.execute(
            """INSERT INTO ai_costs (operation, model, tokens, cost, lead_email)
               VALUES (?, ?, ?, ?, ?)""",
            (cost["operation"], cost["model"], cost["tokens"], cost["cost"], cost["lead_email"])
        )

    conn.commit()
    conn.close()

    print(f"✅ Seeded database with {len(leads)} leads and {len(costs)} cost entries")
    print(f"Database location: {DB_PATH}")

if __name__ == "__main__":
    seed_database()
