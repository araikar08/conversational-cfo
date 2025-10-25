# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Conversational CFO - AI-powered expense tracking for Cal Hacks 12.0 hackathon integrating Lava, Poke, and Fetch.ai sponsor tracks.

## Architecture

**mcp-server/src/server.py** - FastMCP server implementing:
- Receipt OCR using GPT-4o via Lava proxy
- Expense categorization using GPT-4o-mini via Lava proxy
- Conversational workflow with state management
- Poke API integration for messaging

## Development Commands

```bash
# Setup
cd mcp-server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run locally
python src/server.py

# Test with MCP Inspector
npx @modelcontextprotocol/inspector
# Connect to: http://localhost:8000/mcp
```

## Environment Variables

- `LAVA_FORWARD_TOKEN` - Lava API token for LLM routing
- `POKE_API_KEY` - Poke API key for messaging
- `LAVA_BASE_URL` - https://api.lavapayments.com/v1/forward

## Deployment

Configured for Render via `render.yaml`. Set environment variables in Render dashboard before deploying.
