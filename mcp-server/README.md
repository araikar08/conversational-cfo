# Conversational CFO - MCP Server

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)
![tag:lava](https://img.shields.io/badge/lava-FF6B35)
![tag:poke](https://img.shields.io/badge/poke-00D9FF)
![tag:fetchai](https://img.shields.io/badge/fetch.ai-00B8D4)

AI-powered expense tracking through conversational receipt processing for **Cal Hacks 12.0**.

**🏆 Competing in 3 Sponsor Tracks:**
- 💰 **Lava** ($2.5K): Cost-optimized AI routing
- 📱 **Poke** (Ray-Bans + AirPods): MCP automation
- 🤖 **Fetch.ai** ($2.5K): Multi-agent orchestration

## Features

- 🔍 **Smart OCR** - GPT-4o vision for receipt text extraction
- 🧠 **AI Categorization** - GPT-4o-mini for intelligent expense classification
- 💬 **Conversational Flow** - Asks clarifying questions when needed
- 💰 **Lava Integration** - AI cost tracking and routing
- 📱 **Poke Integration** - Email/SMS communication layer
- 🤖 **Fetch.ai Multi-Agent System** - ASI:One compatible agents

## 🤖 Fetch.ai Agents

This project uses **4 intelligent agents** orchestrated via Fetch.ai's uAgents framework:

### Agent Addresses (on Agentverse):

1. **Coordinator Agent** (ASI:One compatible with Chat Protocol)
   - **Name**: `conversational_cfo_coordinator`
   - **Address**: `agent1q279ffgvmxfn5zf2jcuapzdzc9c3acfum66wc350jmgld7swq27kgwy44tz`
   - **Role**: Orchestrates workflow, interfaces with ASI:One

2. **OCR Agent**
   - **Address**: `agent1q2c88xm5aa7sqrthraezm064akywdwzl68e3d0u5zjjj90hu7w0kyusgnpk`
   - **Role**: Receipt image processing via GPT-4o

3. **Categorizer Agent**
   - **Address**: `agent1qgr3w250mfhe03dxfxy2w4xj65h5n0nasq4g4cl0ussfj509734h7djff7n`
   - **Role**: Expense categorization via GPT-4o-mini

4. **Messaging Agent**
   - **Address**: `agent1q227awvsjg0hz9hyh4a275np48drrnehrh30jtrkv0ddhralreazzlkt2zv`
   - **Role**: Poke API communication

### ASI:One Compatibility
The Coordinator Agent implements the **Chat Protocol** and publishes its manifest to Agentverse, making it discoverable through ASI:One for natural language queries.

## Quick Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## Environment Variables

Set these in Render dashboard:

- `LAVA_FORWARD_TOKEN` - Your Lava API token
- `POKE_API_KEY` - Your Poke API key
- `LAVA_BASE_URL` - https://api.lavapayments.com/v1/forward

## Cal Hacks 12.0 Sponsor Tracks

✅ **Lava** - AI model routing and cost tracking
✅ **Poke** - MCP server for conversational messaging
⏳ **Fetch.ai** - Agent orchestration (coming soon)
