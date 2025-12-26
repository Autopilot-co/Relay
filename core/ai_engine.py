"""
Relay - AI Engine
Handles all AI/LLM interactions using Cerebras (via OpenAI SDK)
"""

import logging
import re
from typing import AsyncGenerator, Optional, Tuple
from openai import AsyncOpenAI
from config.settings import settings

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

        logger.info(f"AI Engine initialized with model: {self.model}")

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

Function calling format:
When you need to call an n8n function, use this format in your response:
[CALL:function_name:param1:param2]

Available functions:
- [CALL:list_workflows] - List all workflows
- [CALL:list_workflows:active] - List only active workflows
- [CALL:get_workflow:WORKFLOW_ID] - Get specific workflow details
- [CALL:get_executions] - Get recent executions (all workflows)
- [CALL:get_executions:WORKFLOW_ID] - Get executions for specific workflow
- [CALL:activate_workflow:WORKFLOW_ID] - Activate a workflow
- [CALL:deactivate_workflow:WORKFLOW_ID] - Deactivate a workflow
- [CALL:create_workflow:DESCRIPTION] - Create new workflow (use after gathering ALL requirements)

WORKFLOW GENERATION - n8n JSON Format:

When I call create_workflow, I will ask you to generate valid n8n JSON. Use this structure:

{
  "name": "Workflow Name",
  "nodes": [{"id": "node-1", "name": "Node Name", "type": "n8n-nodes-base.nodeType", "typeVersion": 1, "position": [250, 300], "parameters": {}}],
  "connections": {"Node Name": {"main": [[{"node": "Next Node", "type": "main", "index": 0}]]}},
  "active": false
}

Common node types: scheduleTrigger, webhook, httpRequest, code, if, set, respondToWebhook

Example conversation:
User: "show me my workflows"
You: "Let me check your workflows for you. [CALL:list_workflows]"

User: "why did workflow X fail?"
You: "Let me check the execution history. [CALL:get_executions:X]"

User: "build a workflow to send me daily reports"
You: "I can help with that! A few questions first:
- What kind of reports? (sales, analytics, system status, etc.)
- What data source should I pull from?
- What time should they send?
- Where should I send them? (email, slack, etc.)"

Communication style:
- Use emojis sparingly for status (✅ ❌ ⚠️ 🔍)
- Be conversational, not formal
- Always explain what you're doing before calling functions
- Give context with your answers

Remember: You're a DevOps engineer teammate who happens to work in Slack, not a chatbot."""

    def _parse_function_calls(self, text: str) -> list[Tuple[str, str, list[str]]]:
        """
        Parse function call markers from AI response

        Format: [CALL:function_name:param1:param2]

        Returns:
            List of tuples: (full_match, function_name, [params])
        """
        pattern = r'\[CALL:([^\]]+)\]'
        matches = re.finditer(pattern, text)

        calls = []
        for match in matches:
            full_match = match.group(0)
            call_parts = match.group(1).split(':')
            function_name = call_parts[0]
            params = call_parts[1:] if len(call_parts) > 1 else []
            calls.append((full_match, function_name, params))

        return calls

    async def _execute_function_call(self, function_name: str, params: list[str]) -> str:
        """
        Execute an n8n function call and return formatted result

        Args:
            function_name: Name of the function to call
            params: List of parameters for the function

        Returns:
            Formatted string with function results
        """
        # Import here to avoid circular dependency
        from core.n8n_client import n8n_client

        try:
            # List all workflows
            if function_name == "list_workflows":
                active_only = len(params) > 0 and params[0] == "active"
                workflows = await n8n_client.list_workflows(active_only=active_only)

                if not workflows:
                    return "\n📋 No workflows found."

                result = f"\n📋 **Your Workflows** ({len(workflows)} total):\n"
                for wf in workflows:
                    status = "✅ Active" if wf.get("active") else "⚪ Inactive"
                    name = wf.get("name", "Unnamed")
                    wf_id = wf.get("id", "unknown")
                    result += f"  • {name} - {status} (ID: {wf_id})\n"

                return result

            # Get specific workflow
            elif function_name == "get_workflow":
                if not params:
                    return "\n❌ Error: Missing workflow ID"

                workflow_id = params[0]
                workflow = await n8n_client.get_workflow(workflow_id)

                if not workflow:
                    return f"\n❌ Workflow {workflow_id} not found"

                name = workflow.get("name", "Unnamed")
                active = "✅ Active" if workflow.get("active") else "⚪ Inactive"
                nodes_count = len(workflow.get("nodes", []))

                result = f"\n📄 **Workflow: {name}**\n"
                result += f"  • Status: {active}\n"
                result += f"  • Nodes: {nodes_count}\n"
                result += f"  • ID: {workflow_id}\n"

                return result

            # Get executions
            elif function_name == "get_executions":
                workflow_id = params[0] if params else None
                executions = await n8n_client.get_executions(workflow_id=workflow_id, limit=10)

                if not executions:
                    return "\n📊 No executions found."

                result = f"\n📊 **Recent Executions** ({len(executions)} shown):\n"
                for exe in executions[:5]:  # Show top 5
                    status = exe.get("status", "unknown")
                    status_icon = "✅" if status == "success" else "❌" if status == "error" else "⏸️"
                    wf_name = exe.get("workflowName", "Unknown workflow")
                    started = exe.get("startedAt", "Unknown time")

                    result += f"  {status_icon} {wf_name} - {status}\n"
                    result += f"     Started: {started}\n"

                    if status == "error" and exe.get("error"):
                        error_msg = exe.get("error", {}).get("message", "Unknown error")
                        result += f"     Error: {error_msg[:100]}...\n"

                return result

            # Activate workflow
            elif function_name == "activate_workflow":
                if not params:
                    return "\n❌ Error: Missing workflow ID"

                workflow_id = params[0]
                success = await n8n_client.activate_workflow(workflow_id)

                if success:
                    return f"\n✅ Activated workflow {workflow_id}"
                else:
                    return f"\n❌ Failed to activate workflow {workflow_id}"

            # Deactivate workflow
            elif function_name == "deactivate_workflow":
                if not params:
                    return "\n❌ Error: Missing workflow ID"

                workflow_id = params[0]
                success = await n8n_client.deactivate_workflow(workflow_id)

                if success:
                    return f"\n⚪ Deactivated workflow {workflow_id}"
                else:
                    return f"\n❌ Failed to deactivate workflow {workflow_id}"

            # Create workflow - AI generates JSON
            elif function_name == "create_workflow":
                if not params:
                    return "\n❌ Error: Missing workflow description"

                description = " ".join(params)

                try:
                    # Ask AI to generate workflow JSON
                    import json
                    generation_prompt = f"""Generate valid n8n workflow JSON for: {description}

Return ONLY the JSON, no explanations."""

                    json_response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": self._get_system_prompt()},
                            {"role": "user", "content": generation_prompt}
                        ],
                        max_completion_tokens=self.max_tokens,
                        temperature=0.3,
                        stream=False
                    )

                    workflow_json_text = json_response.choices[0].message.content

                    # Extract JSON
                    if "```json" in workflow_json_text:
                        workflow_json_text = workflow_json_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in workflow_json_text:
                        workflow_json_text = workflow_json_text.split("```")[1].split("```")[0].strip()

                    workflow_data = json.loads(workflow_json_text)

                    # Create in n8n
                    workflow = await n8n_client.create_workflow(workflow_data)

                    if workflow:
                        wf_id = workflow.get("id")
                        wf_name = workflow.get("name")

                        # Save workflow metadata to memory
                        # Note: We don't have channel/user context here, will add later
                        from core.memory import memory
                        memory.save_workflow_built(
                            workflow_id=wf_id,
                            workflow_name=wf_name,
                            description=description,
                            channel="slack",  # Placeholder
                            user="user"  # Placeholder
                        )

                        return f"\n✅ Created: {wf_name} (ID: {wf_id})\n💡 Review in n8n, add credentials, then activate!"
                    else:
                        return "\n❌ Failed to create workflow in n8n"

                except json.JSONDecodeError as e:
                    logger.error(f"AI generated invalid JSON: {e}")
                    return "\n❌ AI generated invalid JSON. Try simpler workflow."
                except Exception as e:
                    logger.error(f"Error creating workflow: {e}")
                    return f"\n❌ Error: {str(e)}"

            else:
                return f"\n❌ Unknown function: {function_name}"

        except Exception as e:
            logger.error(f"Error executing {function_name}: {e}")
            return f"\n❌ Error executing {function_name}: {str(e)}"

    async def process_message(
        self,
        user_message: str,
        conversation_history: Optional[list] = None
    ) -> str:
        """
        Process a user message and return AI response
        Automatically executes any function calls requested by the AI

        Args:
            user_message: The message from the user
            conversation_history: Optional list of previous messages for context

        Returns:
            AI's response as a string (with function results embedded)
        """
        if not self.client:
            return "Sorry, AI features are not configured. Please set CEREBRAS_API_KEY."

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

            # Call Cerebras API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=self.max_tokens,
                temperature=self.temperature,
                reasoning_effort=self.reasoning_effort,
                stream=False
            )

            # Extract response
            ai_response = response.choices[0].message.content

            logger.info(f"AI response generated ({len(ai_response)} chars)")

            # Parse and execute function calls
            function_calls = self._parse_function_calls(ai_response)

            if function_calls:
                logger.info(f"Found {len(function_calls)} function call(s) to execute")

                # Execute each function call and replace in response
                for full_match, function_name, params in function_calls:
                    logger.info(f"Executing: {function_name}({', '.join(params)})")

                    # Execute the function
                    result = await self._execute_function_call(function_name, params)

                    # Replace the marker with the result
                    ai_response = ai_response.replace(full_match, result)

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
