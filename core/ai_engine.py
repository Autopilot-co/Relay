"""
Relay - AI Engine
Handles all AI/LLM interactions using Cerebras (via OpenAI SDK)
Integrates with MCP (Model Context Protocol) for n8n access
"""

import logging
import json
from typing import AsyncGenerator, Optional, Any
from openai import AsyncOpenAI
from config.settings import settings
from core.mcp_client import mcp_manager

logger = logging.getLogger(__name__)

class AIEngine:
    """
    AI Engine for Relay - handles conversations with users
    Uses Cerebras for fast, affordable inference with gpt-oss-120b
    """

    def __init__(self):
        """Initialize the AI engine with Cerebras client"""
        if not settings.cerebras_api_key:
            logger.warning("CEREBRAS_API_KEY not set - AI features will not work")
            self.client = None
            return

        # Initialize OpenAI client pointing to Cerebras endpoint
        self.client = AsyncOpenAI(
            api_key=settings.cerebras_api_key,
            base_url="https://api.cerebras.ai/v1"
        )

        # Model configuration
        self.model = "gpt-oss-120b"
        self.reasoning_effort = "medium"  # low, medium, high
        self.max_tokens = 4096
        self.temperature = 0.7

        # MCP initialization flag
        self.mcp_initialized = False

        logger.info(f"AI Engine initialized with model: {self.model}")

    async def initialize_mcp(self) -> bool:
        """
        Initialize MCP connection to n8n (and other platforms)

        Should be called once during application startup

        Returns:
            True if MCP initialized successfully
        """
        if self.mcp_initialized:
            return True

        try:
            # Connect to n8n MCP server if configured
            if settings.n8n_mcp_url:
                logger.info(f"Connecting to n8n MCP server: {settings.n8n_mcp_url}")
                success = await mcp_manager.add_server("n8n", settings.n8n_mcp_url)

                if success:
                    logger.info("✅ n8n MCP connected successfully")
                    self.mcp_initialized = True

                    # Log available tools
                    tools_desc = mcp_manager.get_tools_description()
                    logger.info(f"MCP tools available:{tools_desc}")

                    return True
                else:
                    logger.error("❌ Failed to connect to n8n MCP server")
                    return False
            else:
                logger.warning("N8N_MCP_URL not set - MCP features disabled")
                return False

        except Exception as e:
            logger.error(f"Error initializing MCP: {e}")
            return False

    def _get_system_prompt(self) -> str:
        """
        System prompt that defines Relay's personality and capabilities

        This tells the AI how to behave as Relay - a DevOps engineer for n8n
        """
        return """You are Relay, an AI DevOps engineer specializing in n8n workflow automation.

Your personality:
- Friendly and conversational (use "hey", "yeah", "cool", casual language)
- Helpful and proactive (suggest improvements, warn about issues)
- Clear and concise (explain technical things in plain English)
- Professional but not robotic (you're a teammate, not a command-line tool)

Your n8n capabilities:
- List workflows and check their status
- Get execution history and analyze failures
- Monitor workflow performance
- Explain errors in plain English
- Build new workflows (MUST ask clarifying questions first)
- Update existing workflows (MUST ask clarifying questions first)
- Optimize workflows based on execution patterns

CRITICAL RULES - When to Ask vs When to Act:

READ-ONLY OPERATIONS (Just do it, no questions needed):
- Listing workflows: "show me my workflows" → Just list them
- Checking status: "what's running?" → Just check executions
- Monitoring: "any failures?" → Just check and report
- Explaining errors: "why did X fail?" → Analyze and explain
- Optimization suggestions: "can this be faster?" → Analyze and suggest

WRITE OPERATIONS (ALWAYS ask clarifying questions first):
- Building workflows: "create a workflow to backup my database"
  → Ask: What database? How often? Where to backup? Then build
- Updating workflows: "add error handling to workflow X"
  → Ask: What kind of errors? How to handle? Then update
- Modifying workflows: "change the schedule to daily"
  → Confirm: Which workflow? What time? Then modify

Why this matters: Read operations are safe. Write operations are destructive and expensive - you MUST understand exactly what the user wants before building anything.

CRITICAL: ASK ONE QUESTION AT A TIME!
- DO NOT list multiple questions at once
- Ask the MOST important question first
- Wait for answer before asking next question
- This creates natural conversation flow

Example - WRONG ❌:
User: "build me a lead generation workflow"
You: "I can help! A few questions:
- Where should I get leads from? (LinkedIn, Reddit, etc.)
- What data do you need? (email, phone, etc.)
- How often should it run?
- Where should results go?"

Example - CORRECT ✅:
User: "build me a lead generation workflow"
You: "Perfect! Let's build that. Where would you like to generate leads from? (LinkedIn, Reddit, or another platform?)"

User: "LinkedIn"
You: "Great choice! What information do you want to collect? (emails, phone numbers, company info, etc.)"

User: "email and phone both"
You: "Got it! How often should this run? (hourly, daily, weekly?)"

...and so on until you have all info, THEN build the workflow.

Function calling:
You have access to n8n tools via MCP (Model Context Protocol). Use the provided tools to:
- List and inspect workflows
- Get execution history and analyze errors
- Activate/deactivate workflows
- Create new workflows

When you need to interact with n8n, simply call the appropriate tool using function calling.
The AI system will automatically handle the MCP communication.

WORKFLOW GENERATION - n8n JSON Format:

When I call create_workflow, I will ask you to generate valid n8n JSON.

CRITICAL JSON FORMATTING RULES:
- Return ONLY valid JSON (no markdown, no explanations)
- NO literal newlines in strings - use \\n for line breaks
- NO line breaks in URLs or string values
- Keep string values on single lines
- Use proper escaping: quotes as \\" and newlines as \\n

Node Types & TypeVersions (use current versions):
- manualTrigger (v1) - Manual trigger button
- scheduleTrigger (v1) - Cron/interval scheduling
- webhook (v1) - Receive HTTP requests
- httpRequest (v4) - Make HTTP API calls
- code (v2) - JavaScript code execution (replaces old "function" node)
- if (v2) - Conditional branching
- set (v3) - Manipulate data
- googleSheets (v4) - Google Sheets operations
- respondToWebhook (v1) - Send webhook response

Code Node Syntax (IMPORTANT):
- Access input data: items[0].json.fieldName (NOT $node["PreviousNode"].json)
- Return format: return items.map(item => ({json: {...}}));
- Multi-line code: use \\n, not actual newlines

Example Valid Workflow:
{
  "name": "Daily API Monitor",
  "active": false,
  "nodes": [
    {
      "id": "1",
      "name": "Every Hour",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1,
      "position": [250, 300],
      "parameters": {
        "rule": {
          "interval": [{"field": "hours", "hoursInterval": 1}]
        }
      }
    },
    {
      "id": "2",
      "name": "Check API",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4,
      "position": [450, 300],
      "parameters": {
        "method": "GET",
        "url": "https://api.example.com/status",
        "options": {}
      }
    },
    {
      "id": "3",
      "name": "Process Response",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [650, 300],
      "parameters": {
        "jsCode": "const status = items[0].json.status;\\nconst uptime = items[0].json.uptime;\\nreturn [{json: {status, uptime, timestamp: new Date().toISOString()}}];"
      }
    }
  ],
  "connections": {
    "Every Hour": {
      "main": [[{"node": "Check API", "type": "main", "index": 0}]]
    },
    "Check API": {
      "main": [[{"node": "Process Response", "type": "main", "index": 0}]]
    }
  }
}

Example conversation:
User: "show me my workflows"
You: "Let me check your workflows for you." [calls n8n_list_workflows tool]

User: "why did workflow X fail?"
You: "Let me check the execution history for workflow X." [calls n8n_get_executions tool]

User: "build a workflow to send me daily reports"
You: "Perfect! Let me start by understanding your requirements. What kind of reports would you like? (sales, analytics, system status, etc.)"

Communication style:
- Use emojis sparingly for status (✅ ❌ ⚠️ 🔍)
- Be conversational, not formal
- Always explain what you're doing before calling functions
- Give context with your answers

Remember: You're a DevOps engineer teammate who happens to work in Slack, not a chatbot."""

    async def _execute_mcp_tool(self, tool_name: str, arguments: dict) -> str:
        """
        Execute an MCP tool and return formatted result

        Args:
            tool_name: Name of the tool to call (e.g., "n8n_list_workflows")
            arguments: Dictionary of arguments for the tool

        Returns:
            Formatted string with tool results
        """
        try:
            # Extract server name from tool name (format: server_toolname)
            parts = tool_name.split("_", 1)
            if len(parts) != 2:
                return f"\n❌ Invalid tool name format: {tool_name}"

            server_name, tool_function = parts

            logger.info(f"Calling MCP tool: {server_name}.{tool_function} with args: {arguments}")

            # Call the MCP tool
            result = await mcp_manager.call_tool(server_name, tool_function, arguments)

            if "error" in result:
                error_msg = result.get("error", {}).get("message", str(result.get("error")))
                logger.error(f"MCP tool error: {error_msg}")
                return f"\n❌ Error: {error_msg}"

            # Format the result for user display
            # The formatting depends on what the tool returns
            # For now, return a JSON representation
            return f"\n✅ Tool result:\n```json\n{json.dumps(result, indent=2)}\n```"

        except Exception as e:
            logger.error(f"Error executing MCP tool {tool_name}: {e}")
            return f"\n❌ Error executing {tool_name}: {str(e)}"

    async def process_message(
        self,
        user_message: str,
        conversation_history: Optional[list] = None
    ) -> str:
        """
        Process a user message and return AI response
        Automatically executes any MCP tool calls requested by the AI

        Args:
            user_message: The message from the user
            conversation_history: Optional list of previous messages for context

        Returns:
            AI's response as a string (with tool results embedded)
        """
        if not self.client:
            return "Sorry, AI features are not configured. Please set CEREBRAS_API_KEY."

        # Initialize MCP if not done yet
        if not self.mcp_initialized:
            await self.initialize_mcp()

        try:
            # Build messages array
            messages = [
                {"role": "system", "content": self._get_system_prompt()}
            ]

            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)

            # Add current user message
            messages.append({"role": "user", "content": user_message})

            logger.info(f"Processing message: {user_message[:100]}...")

            # Get MCP tools for function calling
            tools = mcp_manager.get_all_tools_for_llm() if self.mcp_initialized else None

            # Call Cerebras API with tools
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=self.max_tokens,
                temperature=self.temperature,
                reasoning_effort=self.reasoning_effort,
                tools=tools,
                stream=False
            )

            # Extract response message
            message = response.choices[0].message
            ai_response = message.content or ""

            logger.info(f"AI response generated ({len(ai_response)} chars)")

            # Handle tool calls if present
            if hasattr(message, 'tool_calls') and message.tool_calls:
                logger.info(f"AI requested {len(message.tool_calls)} tool call(s)")

                # Execute each tool call
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

                    # Execute the MCP tool
                    result = await self._execute_mcp_tool(tool_name, tool_args)

                    # Append result to response
                    ai_response += f"\n{result}"

            return ai_response

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"Sorry, I encountered an error: {str(e)}"

    async def process_message_stream(
        self,
        user_message: str,
        conversation_history: Optional[list] = None
    ) -> AsyncGenerator[str, None]:
        """
        Process a message with streaming response (for future use)

        This allows real-time responses as the AI generates them.
        Useful for long responses or to show the AI is "thinking"

        Args:
            user_message: The message from the user
            conversation_history: Optional list of previous messages

        Yields:
            Chunks of the AI response as they're generated
        """
        if not self.client:
            yield "Sorry, AI features are not configured."
            return

        try:
            # Build messages
            messages = [
                {"role": "system", "content": self._get_system_prompt()}
            ]

            if conversation_history:
                messages.extend(conversation_history)

            messages.append({"role": "user", "content": user_message})

            # Stream response
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=self.max_tokens,
                temperature=self.temperature,
                reasoning_effort=self.reasoning_effort,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Error in streaming: {e}")
            yield f"Sorry, I encountered an error: {str(e)}"


# Create a single global instance
# Import this everywhere: from core.ai_engine import ai_engine
ai_engine = AIEngine()
