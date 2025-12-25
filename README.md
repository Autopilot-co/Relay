# Relay - AI DevOps Engineer for Workflows

**Your personal DevOps engineer that builds, deploys, monitors, fixes, and optimizes workflows through natural conversation in Slack.**

---

## What is Relay?

Relay is an AI-powered DevOps engineer for your workflow automation platforms (n8n, Make, Zapier). Instead of manually building workflows, checking dashboards, and debugging issues, you simply chat with Relay:

### Complete Lifecycle Management:

- **Build**: Create workflows from natural language descriptions
- **Deploy**: Activate and configure workflows automatically
- **Monitor**: Track execution status and performance 24/7
- **Debug**: Explain failures in plain English
- **Fix**: Auto-repair common issues or apply fixes on command
- **Optimize**: Improve performance, reduce costs, enhance reliability
- **Control**: Start, stop, pause, and manage executions

**Think of it as:** A DevOps engineer who never sleeps, available in Slack, managing ALL your automation workflows.

**Example Conversations:**
```
You: "hey, did that payment thing run yet?"
Relay: "Yes! Payment workflow completed 5 minutes ago. 
        Processed 12 payments successfully. 
        Total: $3,450. All good! ✅"

You: "build me a workflow that backs up my database daily"
Relay: "Creating workflow: Daily DB Backup
        • Trigger: Cron (2 AM daily)
        • Export PostgreSQL to S3
        • Notify #ops on completion
        ✅ Created and activated!"

You: "the email workflow keeps timing out"
Relay: "Analyzing... Found the issue: Gmail rate limit.
        Fix: Adding retry logic + queue system.
        ✅ Fixed! Testing... Success. Deployed."
```

---

## What Makes Relay a "DevOps Engineer"?

Traditional DevOps engineers for software systems:
- Build deployment pipelines
- Monitor server health
- Fix issues when they arise
- Optimize performance
- Scale infrastructure
- Keep systems running 24/7

**Relay does the same, but for your workflows:**
- Builds workflows from descriptions
- Monitors workflow executions
- Fixes failures automatically
- Optimizes workflow performance
- Scales across platforms (n8n, Make, Zapier)
- Manages everything 24/7 via chat

---

## Current Status (MVP - Phase 1)

✅ **Foundation Complete:**
- FastAPI server (production-ready architecture)
- Configuration management (environment variables, secrets)
- Production-grade logging (console + file, daily rotation)
- Slack webhook (secure message receiving with signature verification)
- Slack handler (bidirectional communication)
- Echo bot (proves full conversation loop works)

⏳ **Phase 2 - Full n8n DevOps Management:**
- **Read**: List workflows, show status, view executions
- **Execute**: Start, stop, pause, resume workflows
- **Monitor**: Track health, performance, success rates
- **Build**: Create workflows from natural language
- **Modify**: Add nodes, change logic, update configurations
- **Fix**: Auto-diagnose and repair issues
- **Optimize**: Improve speed, reduce costs, enhance reliability

⏳ **Phase 3 - AI Intelligence:**
- Natural language understanding (GPT/Claude integration)
- Context-aware conversations
- Proactive monitoring and alerts
- Smart suggestions and best practices

⏳ **Phase 4 - Multi-Platform:**
- Make.com integration
- Zapier integration
- Your custom workflow engine
- Unified management across all platforms

---

## Project Structure

```
Relay/
├── main.py                      # FastAPI entry point
├── requirements.txt             # Python dependencies
├── .env                         # Your secrets (create from .env.example)
│
├── config/
│   └── settings.py              # App configuration
│
├── core/                        # (Coming soon: AI logic)
│
├── integrations/                # (Coming soon: n8n, Make, Zapier)
│
├── platforms/
│   └── slack_handler.py         # Send messages to Slack
│
├── webhooks/
│   └── slack_webhook.py         # Receive messages from Slack
│
├── utils/
│   └── logger.py                # Logging system
│
└── logs/
    └── relay_YYYY-MM-DD.log     # Daily log files
```

---

## Setup Instructions

### Prerequisites

- Python 3.10+
- Slack workspace (for testing)
- ngrok (for local development)

### 1. Install Dependencies

```bash
cd Relay
pip install -r requirements.txt
```

### 2. Create Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Name it **"Relay"**, select your workspace
4. Click **"Create App"**

### 3. Configure Slack App

#### Enable Events API:
1. Go to **"Event Subscriptions"** in left sidebar
2. Toggle **"Enable Events"** to **On**
3. Leave **Request URL** blank for now (we'll fill this after starting server)

#### Add Bot Scopes:
1. Go to **"OAuth & Permissions"** in left sidebar
2. Scroll to **"Scopes"** → **"Bot Token Scopes"**
3. Add these scopes:
   - `chat:write` (send messages)
   - `channels:history` (read channel messages)
   - `app_mentions:read` (when @mentioned)

#### Install to Workspace:
1. Go to **"OAuth & Permissions"**
2. Click **"Install to Workspace"**
3. Click **"Allow"**
4. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)

#### Get Signing Secret:
1. Go to **"Basic Information"** in left sidebar
2. Scroll to **"App Credentials"**
3. Copy the **"Signing Secret"**

### 4. Configure Environment

```bash
# Create .env file
cp .env.example .env

# Edit .env and add your tokens:
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_SIGNING_SECRET=your-secret-here
```

### 5. Start the Server

```bash
uvicorn main:app --reload --port 8000
```

You should see:
```
[2025-12-25 10:00:00] INFO: Initializing Relay...
[2025-12-25 10:00:00] INFO: Relay initialized successfully
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 6. Expose Local Server (ngrok)

In a **new terminal**:

```bash
ngrok http 8000
```

You'll see output like:
```
Forwarding    https://abc123.ngrok-free.app -> http://localhost:8000
```

Copy the **https URL** (e.g., `https://abc123.ngrok-free.app`)

### 7. Configure Slack Webhook URL

1. Go back to https://api.slack.com/apps → Your App
2. Go to **"Event Subscriptions"**
3. Paste your ngrok URL + `/webhooks/slack`:
   ```
   https://abc123.ngrok-free.app/webhooks/slack
   ```
4. Click **"Save Changes"** (Slack will verify the URL)

### 8. Subscribe to Events

Still in **"Event Subscriptions"**:

1. Scroll to **"Subscribe to bot events"**
2. Click **"Add Bot User Event"**
3. Add these events:
   - `message.channels` (messages in channels)
   - `app_mention` (when @mentioned)
4. Click **"Save Changes"**
5. Slack will prompt to **reinstall** - click **"Reinstall App"**

### 9. Test the Bot!

#### Invite Bot to Channel:
1. In Slack, go to any channel
2. Type: `/invite @Relay`

#### Send a Message:
```
You: hello
Relay: You said: hello
```

**It works!** 🎉

---

## Logs

### View Real-Time Logs:

```bash
tail -f logs/relay_$(date +%Y-%m-%d).log
```

### Example Log Output:

```
[2025-12-25 10:00:00] INFO: Initializing Relay...
[2025-12-25 10:00:05] INFO: Slack webhook called
[2025-12-25 10:00:05] INFO: Received Slack event: event_callback
[2025-12-25 10:00:05] INFO: Message from user U123 in channel C456: hello
[2025-12-25 10:00:05] INFO: Sending message to channel C456: You said: hello
[2025-12-25 10:00:06] INFO: Message sent successfully
```

---

## Development

### Check Health:

```bash
curl http://localhost:8000/health
```

### Test Webhook Locally:

```bash
curl -X POST http://localhost:8000/webhooks/slack \
  -H "Content-Type: application/json" \
  -d '{"type":"url_verification","challenge":"test123"}'
```

---

## Next Steps

### Phase 1: Foundation ✅
- [x] FastAPI server (production-ready)
- [x] Slack integration (secure webhooks)
- [x] Bidirectional communication
- [x] Logging system
- [x] Configuration management
- [x] Echo bot (proves loop works)

### Phase 2: n8n DevOps Capabilities
**Read Operations:**
- [ ] Connect to n8n API
- [ ] List all workflows
- [ ] Get workflow details
- [ ] View execution history
- [ ] Check workflow status

**Execute Operations:**
- [ ] Start/stop workflows
- [ ] Pause/resume workflows
- [ ] Trigger manual executions
- [ ] Control execution queues

**Build Operations:**
- [ ] Create workflows from natural language
- [ ] Generate workflow JSON from descriptions
- [ ] Deploy new workflows automatically
- [ ] Validate workflow structure

**Modify Operations:**
- [ ] Add nodes to existing workflows
- [ ] Update workflow configurations
- [ ] Change triggers and schedules
- [ ] Refactor workflow logic

**Fix Operations:**
- [ ] Diagnose workflow failures
- [ ] Auto-fix common issues
- [ ] Apply error handling
- [ ] Add retry logic

**Optimize Operations:**
- [ ] Identify performance bottlenecks
- [ ] Suggest improvements
- [ ] Reduce API calls
- [ ] Optimize data handling

### Phase 3: AI Intelligence
- [ ] OpenAI/Claude integration
- [ ] Natural language understanding
- [ ] Context-aware conversations
- [ ] Intent detection
- [ ] Workflow generation from descriptions
- [ ] Smart error explanations
- [ ] Proactive suggestions
- [ ] Learning from patterns

### Phase 4: Multi-Platform DevOps
- [ ] Make.com integration (full CRUD)
- [ ] Zapier integration (full CRUD)
- [ ] Custom engine support
- [ ] Unified workflow management
- [ ] Cross-platform orchestration
- [ ] Platform-agnostic commands

---

## Architecture

### Current (Phase 1):
```
User in Slack
     ↓
Slack API → ngrok → FastAPI Server → Webhook Handler
                                           ↓
                                      Echo Logic
                                           ↓
                                    Slack Handler → Back to Slack
```

### Target (Full DevOps):
```
User: "Build a backup workflow"
     ↓
Slack → FastAPI → Webhook Handler
                       ↓
                  AI Engine (GPT/Claude)
                  • Understand intent
                  • Generate workflow JSON
                       ↓
                  n8n Client
                  • Create workflow via API
                  • Validate structure
                  • Deploy & activate
                       ↓
                  Monitoring Service
                  • Track execution
                  • Log performance
                  • Alert on issues
                       ↓
                  Slack Handler → "✅ Workflow created and activated!"
```

### Data Flow:
```
Natural Language → AI Understanding → Workflow Operations → Platform APIs → Results → User
```

---

## Troubleshooting

### Bot Doesn't Respond:

1. **Check logs**: `tail -f logs/relay_*.log`
2. **Check ngrok**: Is it still running?
3. **Check Slack events**: api.slack.com/apps → Your App → Event Subscriptions → Retry failed events
4. **Check bot token**: In `.env`, starts with `xoxb-`

### "Invalid Signature" Error:

- Signing secret in `.env` might be wrong
- Check api.slack.com/apps → Your App → Basic Information → Signing Secret

### Bot Not Seeing Messages:

- Invite bot to channel: `/invite @Relay`
- Check bot scopes: Need `channels:history`

---

## Contributing

This is a learning project! Feel free to:
- Report issues
- Suggest features
- Submit pull requests
- Ask questions

---

## License

MIT License - See LICENSE file

---

## The Vision: Universal DevOps Engineer for Workflows

### The Problem:
- Companies use multiple workflow platforms (n8n, Make, Zapier, custom)
- Each requires opening a separate dashboard
- Building workflows manually is time-consuming
- Debugging requires technical expertise
- Monitoring is reactive, not proactive
- No single source of truth

### The Solution: Relay
**One AI DevOps engineer that manages ALL your workflow platforms through natural conversation.**

### What This Means:
```
Instead of:                    With Relay:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Open n8n dashboard       →     "Show all workflows"
Drag nodes manually      →     "Build a backup workflow"
Check logs for errors    →     "Why did payment fail?"
Manually add retry logic →     "Add retry to email workflow"
Monitor multiple tools   →     Proactive alerts in Slack
Write documentation      →     "Explain this workflow"
```

### The End Goal:
**You describe what you need. Relay builds, deploys, monitors, and maintains it.**

No dashboards. No manual work. Just conversation with your AI DevOps engineer.

**Chat with Relay. Build, manage, and optimize everything.** 🚀
