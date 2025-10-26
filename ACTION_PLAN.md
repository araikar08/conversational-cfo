# 🎯 Cal Hacks Action Plan - Saturday Morning

## ⚠️ CRITICAL ISSUE DISCOVERED

**Our Lava integration is using the WRONG authentication format!**

### Current (Wrong):
```python
api_key=LAVA_FORWARD_TOKEN
base_url=f"{LAVA_BASE_URL}?u=https://api.openai.com/v1"
```

### Required (Correct):
```python
lava_forward_token = {
    "secret_key": LAVA_API_KEY,
    "connection_secret": CONNECTION_SECRET,
    "product_secret": PRODUCT_SECRET
}
encoded_token = base64.b64encode(json.dumps(lava_forward_token).encode()).decode()
headers = {"Authorization": f"Bearer {encoded_token}"}
```

---

## 🚨 PRIORITY 1: FIX LAVA INTEGRATION (30 min)

### Why This Matters:
- Current approach might not be tracking costs properly
- Judges will check if we're using Lava correctly
- Tutorial shows the proper way - we must match it

### Steps:

1. **Get Lava Credentials from Dashboard** (5 min)
   - [ ] Login: https://www.lavapayments.com/
   - [ ] Find: `secret_key` (your API key)
   - [ ] Find: `connection_secret` (connection ID)
   - [ ] Find: `product_secret` (product ID)
   - [ ] Add to `.env` file

2. **Update server.py** (15 min)
   - [ ] Import `base64` and `json`
   - [ ] Create forward token function
   - [ ] Update `ocr_llm` and `reasoning_llm` to use proper auth
   - [ ] Test locally

3. **Verify It Works** (10 min)
   - [ ] Process a receipt
   - [ ] Check Lava dashboard shows the request
   - [ ] Verify cost tracking updates

---

## 🚨 PRIORITY 2: VERIFY FETCH.AI AGENT (10 min)

### Critical for Prize Eligibility!

1. **Login to Agentverse** (2 min)
   - [ ] Go to: https://agentverse.ai
   - [ ] Login with your credentials

2. **Find Your Agent** (2 min)
   - [ ] Navigate to "My Agents"
   - [ ] Find "Conversational CFO" or "conversational_cfo_coordinator"
   - [ ] Verify status is "Active" ✓

3. **Add Required Tags** (3 min)
   - [ ] Click on your agent
   - [ ] Find "Tags" or "Categories" section
   - [ ] **MUST ADD:** `innovationlab`
   - [ ] **MUST ADD:** `hackathon`
   - [ ] Save changes

4. **Take Screenshot** (3 min)
   - [ ] Screenshot showing:
     - Agent name: "Conversational CFO"
     - Status: Active
     - Tags: innovationlab, hackathon
     - Chat Protocol: Enabled
   - [ ] Save for demo presentation

---

## 🚨 PRIORITY 3: CHECK POKE INTEGRATION (15 min)

### Option A: Set Up Webhook (Ideal)

1. **Login to Poke** (2 min)
   - [ ] Access your Poke account
   - [ ] Navigate to "Integrations" or "Webhooks"

2. **Configure Webhook** (10 min)
   - [ ] Create new webhook
   - [ ] URL: `https://conversational-cfo.onrender.com/webhook/poke`
   - [ ] Method: POST
   - [ ] Content-Type: application/json
   - [ ] Expected payload format:
     ```json
     {
       "user_id": "string",
       "message": "string",
       "attachments": [{"type": "image", "url": "string"}]
     }
     ```

3. **Test** (3 min)
   - [ ] Send test receipt via text/email
   - [ ] Check Render logs for webhook hit
   - [ ] Verify response comes back

### Option B: Demo Via MCP Inspector (Backup)
- [ ] If Poke webhook doesn't work, use MCP Inspector for demo
- [ ] Explain: "Poke would trigger this endpoint in production"

---

## 🧪 PRIORITY 4: END-TO-END TESTING (20 min)

### 1. Start Local Environment (5 min)

```bash
cd /Users/aryanraikar/conversational-cfo/mcp-server
source .venv/bin/activate
python src/server.py
```

In another terminal:
```bash
npx @modelcontextprotocol/inspector
```

### 2. Test All Features (15 min)

#### Test 1: Process Receipt
- [ ] Open: http://localhost:6277
- [ ] Call `process_receipt` tool
- [ ] Input:
  ```json
  {
    "user_id": "demo_user_001",
    "image_url": "https://templates.invoicehome.com/receipt-template-us-neat-750px.png",
    "message": ""
  }
  ```
- [ ] **Watch terminal logs** for:
  - 🤖 Fetch.ai agent workflow
  - 💰 Lava cost tracking
  - ✅ Agent delegation steps
- [ ] **Check response** includes:
  - `_agent_metadata` with agent addresses
  - `_lava_cost_data` with costs

#### Test 2: Check User Costs
- [ ] Call `get_user_costs` tool
- [ ] Input: `{"user_id": "demo_user_001"}`
- [ ] **Verify shows:**
  - Total AI cost
  - Receipts processed
  - Cost breakdown (GPT-4o vs GPT-4o-mini)

#### Test 3: Check Agent Status
- [ ] Call `check_agent_status` tool
- [ ] No input needed
- [ ] **Verify shows:**
  - All 4 agents with addresses
  - ASI:One compatibility: true
  - Chat Protocol: enabled

---

## 📋 AFTER FIXES: COMMIT & DEPLOY (10 min)

### 1. Commit Changes
```bash
git add -A
git commit -m "fix: correct Lava Build authentication format

Use proper forward token with secret_key, connection_secret, product_secret
as required by Lava Build API. Ensures proper cost tracking and usage analytics."
git push
```

### 2. Update Render Environment Variables
- [ ] Go to: https://dashboard.render.com
- [ ] Find: "conversational-cfo" service
- [ ] Add environment variables:
  - `LAVA_API_KEY`
  - `LAVA_CONNECTION_SECRET`
  - `LAVA_PRODUCT_SECRET`
- [ ] Redeploy

### 3. Verify Production Works
```bash
curl https://conversational-cfo.onrender.com/mcp
```

---

## 📸 SCREENSHOTS TO CAPTURE

Before judging, take screenshots of:

1. **Lava Dashboard**
   - [ ] API usage graph
   - [ ] Cost breakdown
   - [ ] Request count

2. **Agentverse Dashboard**
   - [ ] Agent status page
   - [ ] Shows "innovationlab" tag
   - [ ] Chat Protocol enabled

3. **MCP Inspector**
   - [ ] Receipt processing result
   - [ ] Response with `_agent_metadata`
   - [ ] Response with `_lava_cost_data`

4. **Terminal Logs**
   - [ ] Agent workflow delegation
   - [ ] Lava cost tracking logs
   - [ ] All 4 agents completing tasks

---

## 🎤 UPDATED DEMO TALKING POINTS

### For Lava:
✅ "We use Lava Build's forward token API with proper authentication - secret_key, connection_secret, and product_secret. This enables per-user cost tracking. See this receipt? Cost $0.02 - GPT-4o for vision ($5/1M tokens), GPT-4o-mini for text ($0.15/1M tokens). That's 97% savings. Call `get_user_costs` to see analytics."

### For Fetch.ai:
✅ "4-agent system registered on Agentverse with Innovation Lab tags. Watch the terminal - Coordinator delegates to OCR Agent, then Categorizer, then Messaging. Every response includes agent metadata showing addresses. It implements Chat Protocol for ASI:One discoverability. Call `check_agent_status` to see the architecture."

### For Poke:
✅ "Poke's MCP server enables conversational expense tracking. Our webhook at `/webhook/poke` receives messages, the Fetch.ai agents process them, and Poke delivers responses. Multi-turn conversations work through state management."

---

## ⏰ TIME ESTIMATES

| Task | Time | Priority |
|------|------|----------|
| Fix Lava Integration | 30 min | 🔴 CRITICAL |
| Verify Fetch.ai Agent | 10 min | 🔴 CRITICAL |
| Check Poke | 15 min | 🟡 MEDIUM |
| End-to-End Testing | 20 min | 🔴 CRITICAL |
| Commit & Deploy | 10 min | 🔴 CRITICAL |
| Screenshots | 10 min | 🟡 MEDIUM |

**Total: ~95 minutes (1.5 hours)**

---

## 🚦 STATUS CHECKLIST

Before judging:
- [ ] Lava using correct auth format (secret_key + connection_secret + product_secret)
- [ ] Lava dashboard accessible and showing usage
- [ ] Fetch.ai agent tagged with "innovationlab" (REQUIRED!)
- [ ] Fetch.ai agent shows "Active" status
- [ ] Poke webhook configured OR backup plan ready
- [ ] All 3 MCP tools tested and working
- [ ] Terminal logs show agent delegation
- [ ] Screenshots captured
- [ ] Production deployment updated
- [ ] Can explain every part of the code

---

## 🎯 THE FIX YOU NEED TO DO FIRST

**Priority 1: Fix Lava Integration**

This is the most important because:
1. Tutorial shows you're not using it correctly
2. Judges will check if you understand Lava Build
3. Current approach might not track costs properly

Once Lava is fixed, the rest is verification/testing.

Ready to start? Let's fix Lava first! 🚀
