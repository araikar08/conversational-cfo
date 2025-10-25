import os
from uagents_core.utils.registration import (
    register_chat_agent,
    RegistrationRequestCredentials,
)

# Agent seed phrase from agents.py
AGENT_SEED_PHRASE = "coordinator_seed_conversational_cfo"

# Get Agentverse key from environment variable
# You need to set this before running: export AGENTVERSE_KEY="your_key_here"
AGENTVERSE_KEY = os.environ.get("AGENTVERSE_KEY")

if not AGENTVERSE_KEY:
    print("❌ ERROR: AGENTVERSE_KEY environment variable not set!")
    print("Please run: export AGENTVERSE_KEY='your_key_from_agentverse'")
    exit(1)

print("🚀 Registering Conversational CFO agent on Agentverse...")
print(f"   Name: Conversational CFO")
print(f"   Endpoint: https://conversational-cfo.onrender.com/mcp")
print(f"   Seed: {AGENT_SEED_PHRASE}")
print()

try:
    register_chat_agent(
        "Conversational CFO",
        "https://conversational-cfo.onrender.com/mcp",
        active=True,
        credentials=RegistrationRequestCredentials(
            agentverse_api_key=AGENTVERSE_KEY,
            agent_seed_phrase=AGENT_SEED_PHRASE,
        ),
    )
    print("✅ SUCCESS! Agent registered on Agentverse!")
    print("   Your agent is now discoverable on ASI:One")
except Exception as e:
    print(f"❌ ERROR: {e}")
    print("   Please check your Agentverse key and try again")
