#!/usr/bin/env python3
"""
Batch enrich leads to demonstrate Lava scale and cost savings
Adds 20 test leads and enriches them all
"""

import sqlite3
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sdr_server import enrich_contact, EnrichInput

DB_PATH = Path(__file__).parent / "leads.db"

# 20 realistic test leads for Cal Hacks demo
test_leads = [
    {"email": "alice@techcorp.io", "context": "Met at Cal Hacks career fair, CS major"},
    {"email": "bob@startup.ai", "context": "Pitched at demo day, AI/ML focus"},
    {"email": "carol@growth.co", "context": "Sales VP, looking for automation"},
    {"email": "david@enterprise.com", "context": "CTO of 500-person company"},
    {"email": "eve@innovate.tech", "context": "Product manager, interested in SDR tools"},
    {"email": "frank@venture.capital", "context": "Investor, wants to see ROI data"},
    {"email": "grace@saas.io", "context": "Founder, recently raised seed round"},
    {"email": "henry@consulting.com", "context": "Consultant helping clients with sales ops"},
    {"email": "iris@marketing.agency", "context": "Agency owner, 20+ clients"},
    {"email": "jack@ecommerce.shop", "context": "D2C brand, scaling outbound"},
    {"email": "kate@fintech.app", "context": "B2B fintech, hiring sales team"},
    {"email": "leo@healthtech.io", "context": "Healthcare startup, compliance focused"},
    {"email": "maya@edtech.com", "context": "EdTech platform, B2B sales"},
    {"email": "noah@logistics.co", "context": "Supply chain SaaS, enterprise deals"},
    {"email": "olivia@crypto.fund", "context": "Crypto fund, exploring sales automation"},
    {"email": "paul@developer.tools", "context": "Dev tools company, PLG motion"},
    {"email": "quinn@analytics.ai", "context": "Data analytics platform, outbound heavy"},
    {"email": "rachel@remote.work", "context": "Remote work tools, global team"},
    {"email": "sam@security.io", "context": "Cybersecurity, long sales cycles"},
    {"email": "tina@video.tech", "context": "Video conferencing startup, rapid growth"}
]

def batch_enrich():
    """Add and enrich 20 leads to demonstrate Lava scale"""
    print("🚀 Starting batch enrichment of 20 leads...")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    added = 0
    enriched = 0

    for lead in test_leads:
        # Add lead to database
        try:
            cursor.execute(
                """INSERT INTO leads (email, context, stage)
                   VALUES (?, ?, 'new')""",
                (lead["email"], lead["context"])
            )
            conn.commit()
            added += 1
            print(f"✅ Added: {lead['email']}")
        except sqlite3.IntegrityError:
            print(f"⏭️  Skip (exists): {lead['email']}")
            continue

        # Enrich the lead
        try:
            result = enrich_contact(EnrichInput(email=lead["email"]))
            enriched += 1
            print(f"🔍 Enriched: {lead['email']}")
        except Exception as e:
            print(f"❌ Error enriching {lead['email']}: {e}")

        # Small delay to avoid rate limits
        time.sleep(0.5)

    conn.close()

    print("=" * 60)
    print(f"✅ Batch complete!")
    print(f"   - Added: {added} leads")
    print(f"   - Enriched: {enriched} leads")
    print(f"   - Estimated Lava cost: ${enriched * 0.0025:.4f}")
    print(f"   - Without Lava routing: ${enriched * 0.0125:.4f}")
    print(f"   - Savings: 80%!")
    print("")
    print("💰 Check your Lava dashboard for updated usage!")
    print("🔗 https://build.lavapayments.com")

if __name__ == "__main__":
    batch_enrich()
