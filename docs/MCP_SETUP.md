# MCP (Model Context Protocol) Setup Guide

## What is MCP?

MCP = **"USB-C for AI"** - An open standard by Anthropic for connecting AI applications to external tools.

**Architecture:**
```
Relay (Host) → MCP Client → MCP Server (n8n/Zapier/Make) → Actual Platform
```

**Why MCP?**
- ✅ Standardized protocol (no custom REST API code)
- ✅ AI knows ALL platform capabilities automatically
- ✅ Auto-updates when platforms add new features
- ✅ One codebase for multiple platforms

---

## Step 1: Install n8n MCP Server

### Option A: Using npx (Easiest)

```bash
# No installation needed! Run directly:
npx @modelcontextprotocol/server-n8n \
  --api-key YOUR_N8N_API_KEY \
  --base-url https://your-n8n.com
```

### Option B: Install Globally

```bash
# Install n8n MCP server
npm install -g @czlonkowski/n8n-mcp

# Run the server
n8n-mcp --api-key YOUR_N8N_API_KEY --base-url https://your-n8n.com
```

### Option C: Docker (Recommended for Production)

```bash
# Run n8n MCP server in Docker
docker run -d \
  --name n8n-mcp \
  -p 3000:3000 \
  -e N8N_API_KEY=YOUR_N8N_API_KEY \
  -e N8N_BASE_URL=https://your-n8n.com \
  czlonkowski/n8n-mcp
```

---

## Step 2: Get Your n8n API Key

1. Open your n8n instance: `https://your-n8n-domain.com`
2. Go to **Settings** → **API**
3. Click **"Create an API key"**
4. Copy the key (starts with `n8n_api_...`)
5. Save it securely

---

## Step 3: Configure Relay

Add to your `.env` file:

```bash
# n8n Configuration
N8N_API_URL=https://your-n8n.com/api/v1
N8N_API_KEY=n8n_api_xxxxxxxxxxxxxxxx

# n8n MCP Server URL
N8N_MCP_URL=http://localhost:3000/mcp

# Optional: Other MCP servers
# ZAPIER_MCP_URL=https://zapier.com/mcp
# MAKE_MCP_URL=https://make.com/mcp
```

---

## Step 4: Test MCP Connection

Run the test script:

```bash
python test_mcp_connection.py
```

You should see:
```
✅ MCP initialized
✅ Discovered 50+ tools
✅ Tool: create_workflow - Create a new n8n workflow
✅ Tool: list_workflows - List all workflows
✅ Tool: execute_workflow - Trigger workflow execution
...
```

---

## MCP vs REST API Comparison

### Before (REST API):
```python
# Manual function calling
if "[CALL:create_workflow:description]" in ai_response:
    # Parse manually
    # Generate JSON ourselves
    # POST to n8n REST API
    # Handle errors
```

### After (MCP):
```python
# AI has direct n8n access via MCP
mcp_manager.add_server("n8n", "http://localhost:3000/mcp")

# AI automatically knows ALL n8n capabilities
# Tools available to AI via function calling
# No manual parsing needed
```

---

## How Relay Uses MCP

```
User in Slack: "Build LinkedIn scraper"
    ↓
Relay AI (Claude + MCP tools)
    ↓
AI decides to call: n8n_create_workflow
    ↓
MCP Client → n8n MCP Server
    ↓
n8n creates workflow
    ↓
MCP returns workflow_id
    ↓
Relay: "✅ Workflow created! ID: 123"
```

---

## Troubleshooting

### MCP server not starting

```bash
# Check if port 3000 is free
lsof -i:3000

# Kill process if needed
kill -9 <PID>

# Try different port
n8n-mcp --api-key KEY --base-url URL --port 3001
```

### MCP connection failing

```bash
# Test MCP server directly
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-06-18",
      "capabilities": {}
    }
  }'

# Should return server info
```

### AI not seeing tools

```bash
# Check if MCP initialized
# In Relay logs, you should see:
# "MCP initialized: 50 tools, 5 resources"

# If not, check .env has correct N8N_MCP_URL
```

---

## Advanced: Multiple Platforms

### Connect to n8n + Zapier + Make

```python
# In main.py or startup
from core.mcp_client import mcp_manager

# Add n8n
await mcp_manager.add_server("n8n", "http://localhost:3000/mcp")

# Add Zapier (if user has Zapier account)
await mcp_manager.add_server("zapier", "https://zapier.com/mcp")

# Add Make (if user has Make account)
await mcp_manager.add_server("make", "https://make.com/mcp")

# Now AI has access to ALL platforms!
```

---

## Resources

- **MCP Specification:** https://modelcontextprotocol.io/
- **n8n MCP GitHub:** https://github.com/czlonkowski/n8n-mcp
- **MCP for Beginners:** https://github.com/microsoft/mcp-for-beginners
- **Anthropic MCP Docs:** https://www.anthropic.com/news/model-context-protocol
