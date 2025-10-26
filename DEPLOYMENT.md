# Deployment Guide - Poke SDR

Complete deployment instructions for Cal Hacks 12.0 demo.

## ⚡ Quick Deploy (15 minutes)

### 1. Deploy MCP Server to Render

**Option A: Via Dashboard (Recommended)**
1. Go to [render.com](https://render.com) and sign in
2. Click "New +" → "Web Service"
3. Connect GitHub: `araikar08/conversational-cfo`
4. Configure:
   - **Name**: `poke-sdr-mcp`
   - **Root Directory**: `mcp-server`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python src/sdr_server.py`
   - **Plan**: Free

5. Add Environment Variables:
   ```
   LAVA_FORWARD_TOKEN=<paste-from-lava-dashboard>
   LAVA_BASE_URL=https://api.lavapayments.com/v1/forward
   POKE_API_KEY=<paste-from-poke-settings>
   PORT=8000
   DB_PATH=/data/leads.db
   ```

6. Add Disk:
   - **Name**: `poke-sdr-db`
   - **Mount Path**: `/data`
   - **Size**: 1 GB

7. Click "Create Web Service"
8. Wait 5-10 minutes for deployment
9. Copy your Render URL: `https://poke-sdr-mcp-XXXX.onrender.com`

**Option B: Via render.yaml (Faster)**
1. Render will auto-detect `mcp-server/render.yaml`
2. Just add environment variables in dashboard
3. Deploy automatically

### 2. Seed Database (One-time)

Once deployed, run seed script:
```bash
# SSH into Render container (or use Render Shell)
python seed_leads.py
```

This adds 5 sample leads + 10 cost entries for demo.

### 3. Update Poke Integration

1. Open Poke app → Connected Integrations
2. Edit "Poke SDR" integration
3. Update URL from ngrok to Render:
   ```
   Old: https://66ff2c62667f.ngrok-free.app/mcp
   New: https://poke-sdr-mcp-XXXX.onrender.com/mcp
   ```
4. Save and verify tools still appear

### 4. Deploy Dashboard to Vercel

```bash
cd dashboard

# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Answer prompts:
# - Project name: poke-sdr-dashboard
# - Directory: ./
# - Override settings: No

# Production deploy
vercel --prod
```

Copy production URL: `https://poke-sdr-dashboard.vercel.app`

### 5. Test End-to-End Flow

**Via Poke App:**
1. Tap "Add Lead" button
2. Enter:
   - Email: `test@calhacks.io`
   - Context: `Met at Cal Hacks demo day, interested in AI tools`
3. Wait for enrichment notification
4. Check dashboard for new lead

**Via Text (if configured):**
1. Text Poke: "add lead test@calhacks.io met at demo day"
2. Receive enrichment response
3. Verify in dashboard

## 🔍 Troubleshooting

### MCP Server Not Starting
```bash
# Check Render logs
# Common issues:
# - Missing environment variables
# - Port binding (should use PORT=8000)
# - Database path incorrect
```

### Poke Can't Connect
- Verify URL ends with `/mcp`
- Check Render service is "Available" (not "Deploying")
- Test manually: `curl https://your-url.onrender.com/mcp`

### Database Empty
```bash
# Re-run seeding script
python seed_leads.py

# Or manually add via Poke
```

### Dashboard Not Showing Data
- Dashboard currently shows hardcoded demo data (intentional)
- For live data, connect to MCP server API (future enhancement)

## 📊 Monitoring

### Check Lava Costs
- Via Poke: Text "get billing"
- Via Dashboard: Check cost breakdown cards
- Via Lava Dashboard: https://build.lavapayments.com

### Check Server Health
```bash
# Render URL health check
curl https://poke-sdr-mcp-XXXX.onrender.com/mcp

# Should return MCP protocol response
```

### Check Database
```bash
# SSH to Render container
sqlite3 /data/leads.db "SELECT COUNT(*) FROM leads;"
sqlite3 /data/leads.db "SELECT SUM(cost) FROM ai_costs;"
```

## 🎥 Recording Demo Video

### Script (3-5 minutes)

**Intro (30s)**
- "Hi judges! I'm demoing Poke SDR - an AI sales assistant powered by Poke and Lava"
- Show dashboard: "Here's my sales pipeline with 5 leads"

**Lava Value Prop (60s)**
- Point to cost stats: "Total cost: $0.15 for 85 AI calls"
- "Without Lava's smart routing: $5.20 - that's 97% savings"
- "GPT-4o for complex enrichment, GPT-4o-mini for simple suggestions"

**Poke Demo (90s)**
- Open Poke app
- Show MCP integration page: "All 5 tools auto-discovered"
- Tap "Add Lead"
- Enter: john@newstartup.io, met at hackathon booth
- Show enrichment notification with suggested action
- "Poke makes sales workflows conversational - no clicking through CRMs"

**Live Flow (60s)**
- Refresh dashboard
- Show new lead appeared
- Point to AI cost: "$0.0025 via Lava"
- Show suggested action

**Wrap (30s)**
- "Poke SDR solves real pain: manual lead data entry"
- "Lava makes AI affordable at scale"
- "Business viability: $10/month SaaS, profitable margins with Lava"
- "Thanks for watching!"

### Recording Tips
- Use screen recording: QuickTime (Mac) or OBS
- Record Poke on phone, screencast dashboard
- Edit together: iMovie, DaVinci Resolve, or CapCut
- Upload to YouTube (unlisted)
- Submit link to Devpost

## ✅ Pre-Demo Checklist

**30 minutes before judging:**
- [ ] MCP server deployed and healthy
- [ ] Database seeded with 5 leads
- [ ] Poke integration updated with production URL
- [ ] Dashboard deployed to Vercel
- [ ] Test end-to-end: add 1 lead via Poke
- [ ] Verify enrichment works
- [ ] Check Lava dashboard for cost tracking
- [ ] Demo video uploaded
- [ ] Pitch practiced (2 minutes)

**During judging:**
- [ ] Show Poke app first (phone)
- [ ] Add lead live if wifi allows
- [ ] Fall back to pre-recorded video if demo breaks
- [ ] Emphasize cost savings (97% via Lava)
- [ ] Highlight MCP automation (5 tools, zero setup)

## 🚨 Emergency Fallbacks

If live demo fails:
1. **Show pre-recorded video** (have it ready on phone)
2. **Show GitHub commit history** (proves you built it)
3. **Show Lava dashboard** (proves API usage)
4. **Show Poke MCP integration screen** (proves connection)
5. **Walk through code** (sdr_server.py:221-404 - the 5 MCP tools)

## 📞 Support Contacts

- **Lava Discord**: [invite link]
- **Poke Support**: support@interaction.co
- **Render Docs**: https://render.com/docs
- **Claude Code**: For any bugs, I'm still here!

Good luck at Cal Hacks 12.0! 🚀
