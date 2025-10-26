# Poke SDR - AI Sales Assistant

![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)
![tag:lava](https://img.shields.io/badge/lava-FF6B35)
![tag:poke](https://img.shields.io/badge/poke-00D9FF)
![tag:calhacks12](https://img.shields.io/badge/Cal_Hacks_12.0-FFD700)

**AI-powered sales development rep assistant** with conversational lead management via Poke + cost-efficient AI routing via Lava.

Built for **Cal Hacks 12.0** - competing for:
- 💰 **Lava** ($2.5K): Smart multi-model routing for 80%+ cost savings
- 📱 **Poke** (Meta Ray-Bans + AirPods Pro 3): MCP automation for text-based sales workflows

## 🚀 Features

### MCP Tools (5 Total)
1. **add_lead** - Add new leads to your pipeline with context
2. **enrich_contact** - AI-powered profile enrichment (LinkedIn-style data)
3. **suggest_action** - Intelligent next action recommendations
4. **search_leads** - Full-text search across your pipeline
5. **get_billing** - Real-time Lava cost analytics

### Lava Cost Optimization
- **GPT-4o** ($5/1M tokens) for complex enrichment tasks
- **GPT-4o-mini** ($0.15/1M tokens) for simple suggestions
- **Result**: $0.0025/lead vs $0.012 without routing = **80% savings**
- Per-operation cost tracking stored in SQLite

### Poke Conversational Interface
- Text to add leads: "add lead john@startup.io met at Cal Hacks"
- Get enriched profiles automatically
- Receive AI-suggested next actions
- Query pipeline via natural language

### Tech Stack
- **FastMCP 2.12.5** - MCP server framework
- **SQLite** - Persistent lead database
- **LangChain** - LLM orchestration
- **Lava Proxy** - Multi-model routing
- **React + Vite + Tailwind** - Sales dashboard

## 📊 Demo Data

Database seeded with 5 sample leads:
- John Smith @ TechStartup (Demo stage)
- Sarah Johnson @ Growth Co (Contacted)
- Mike Chen @ Enterprise Corp (New)
- Emily Davis @ Startup AI (Contacted)
- Alex Martinez @ Innovate Tech (New)

Total AI operations tracked: 10 (5 enrichments + 5 suggestions)
Total cost: ~$0.0125 via Lava routing

## 🎯 Quick Deploy to Render

1. **Create new Web Service** on [Render](https://render.com)
2. **Connect GitHub repo**: `araikar08/conversational-cfo`
3. **Set root directory**: `mcp-server`
4. **Environment variables**:
   ```
   LAVA_FORWARD_TOKEN=<your-lava-token>
   LAVA_BASE_URL=https://api.lavapayments.com/v1/forward
   POKE_API_KEY=<your-poke-key>
   PORT=8000
   DB_PATH=/data/leads.db
   ```
5. **Deploy** - Render will use `render.yaml` configuration

## 🔌 Connect to Poke

1. Open Poke app → Automations → Add Integration
2. Enter MCP server URL: `https://your-render-url.onrender.com/mcp`
3. Poke will auto-discover all 5 tools
4. Start texting commands like "add lead jane@example.com met at conference"

## 🏃 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your keys

# Seed database
python seed_leads.py

# Start MCP server
python src/sdr_server.py

# In another terminal, run dashboard
cd ../dashboard
npm install
npm run dev
```

Server runs on `http://localhost:8000/mcp`
Dashboard runs on `http://localhost:5173`

## 📱 Poke Integration Status

✅ MCP server running
✅ All 5 tools discovered
✅ Conversational interface active
⏳ End-to-end flow testing in progress

## 💰 Lava Integration Status

✅ Multi-model routing configured
✅ Cost tracking per operation
✅ Real-time analytics via get_billing()
✅ 80% cost savings vs GPT-4o-only approach

## 📋 Database Schema

**leads table:**
- email, name, company, title, context, notes, tags
- stage (new/contacted/demo/closed)
- next_action, enriched (boolean)
- created_at, updated_at

**ai_costs table:**
- operation, model, tokens, cost
- lead_email (foreign key)
- timestamp

## 🎥 Demo Video

Coming soon - will demonstrate:
1. Adding lead via Poke text message
2. Automatic enrichment + action suggestion
3. Dashboard showing pipeline + Lava cost savings
4. End-to-end conversational workflow

## 🏆 Cal Hacks 12.0

**Submission deadline**: Sunday 10:30 AM PDT
**Live demo**: Sunday morning
**Judging**: Lava + Poke sponsor booths
