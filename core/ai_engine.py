"""
Relay - AI Engine
Handles all AI/LLM interactions using Cerebras (via OpenAI SDK)
"""

import logging
from typing import AsyncGenerator, Optional
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

Your capabilities (what you'll be able to do):
- Monitor n8n workflows 24/7
- Explain errors in plain English
- Fix common workflow issues
- Build new workflows from descriptions
- Optimize workflow performance
- Answer questions about workflows

Current phase: Basic conversation (n8n integration coming soon)

Communication style:
- Use emojis sparingly for status (✅ ❌ ⚠️ 🔍)
- Be conversational, not formal
- Ask clarifying questions when needed
- Give context with your answers

Remember: You're a DevOps engineer teammate who happens to work in Slack, not a chatbot."""

    async def process_message(
        self,
        user_message: str,
        conversation_history: Optional[list] = None
    ) -> str:
        """
        Process a user message and return AI response

        Args:
            user_message: The message from the user
            conversation_history: Optional list of previous messages for context

        Returns:
            AI's response as a string
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
                stream=False  # Start with non-streaming for simplicity
            )

            # Extract response
            ai_response = response.choices[0].message.content

            logger.info(f"AI response generated ({len(ai_response)} chars)")

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
