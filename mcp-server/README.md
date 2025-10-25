# Conversational CFO - MCP Server

AI-powered expense tracking through conversational receipt processing for Cal Hacks 12.0.

## Features

- 🔍 **Smart OCR** - GPT-4o vision for receipt text extraction
- 🧠 **AI Categorization** - GPT-4o-mini for intelligent expense classification
- 💬 **Conversational Flow** - Asks clarifying questions when needed
- 💰 **Lava Integration** - AI cost tracking and routing
- 📱 **Poke Integration** - Email/SMS communication layer

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
