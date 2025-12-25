"""
Relay - Slack Handler
Sends messages TO Slack (responses, notifications, etc.)

This is the OUTPUT side of the Slack integration.
"""

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from utils.logger import logger
from typing import Optional


class SlackHandler:
    """
    Handles sending messages to Slack
    
    Uses the Slack WebClient to post messages, reply in threads,
    and send formatted responses to users.
    """
    
    def __init__(self, bot_token: str):
        """
        Initialize the Slack handler
        
        Args:
            bot_token: Your Slack bot token (starts with xoxb-)
        """
        self.client = WebClient(token=bot_token)
        logger.info("Slack handler initialized")
    
    
    async def send_message(
        self, 
        channel: str, 
        text: str,
        thread_ts: Optional[str] = None
    ) -> dict:
        """
        Send a message to a Slack channel
        
        Args:
            channel: Channel ID (e.g., "C123456789")
            text: Message text to send
            thread_ts: Optional thread timestamp to reply in thread
            
        Returns:
            dict: Slack API response
            
        Example:
            await send_message("C123456", "Hello from Relay!")
            await send_message("C123456", "Reply", thread_ts="1234.5678")
        """
        
        try:
            # Log what we're sending
            logger.info(f"Sending message to channel {channel}: {text[:50]}...")
            
            # Send the message via Slack API
            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
                thread_ts=thread_ts  # Reply in thread if provided
            )
            
            # Log success
            logger.info(f"Message sent successfully (ts: {response['ts']})")
            
            return {
                "ok": True,
                "channel": response["channel"],
                "ts": response["ts"]  # timestamp = message ID
            }
            
        except SlackApiError as e:
            # Handle Slack-specific errors
            error_msg = e.response["error"]
            logger.error(f"Slack API error: {error_msg}")
            
            return {
                "ok": False,
                "error": error_msg
            }
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error sending message: {e}")
            
            return {
                "ok": False,
                "error": str(e)
            }
    
    
    async def send_formatted_message(
        self,
        channel: str,
        blocks: list,
        text: str = "",
        thread_ts: Optional[str] = None
    ) -> dict:
        """
        Send a formatted message with Slack Block Kit
        
        Block Kit allows rich formatting: buttons, sections, images, etc.
        This is for later when we want prettier messages.
        
        Args:
            channel: Channel ID
            blocks: List of Slack Block Kit blocks
            text: Fallback text for notifications
            thread_ts: Optional thread to reply in
            
        Returns:
            dict: Slack API response
            
        Example:
            blocks = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Payment Workflow*\nStatus: ✅ Success"}
                }
            ]
            await send_formatted_message("C123", blocks, "Payment succeeded")
        """
        
        try:
            logger.info(f"Sending formatted message to {channel}")
            
            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=text,  # Fallback for notifications
                thread_ts=thread_ts
            )
            
            logger.info("Formatted message sent successfully")
            
            return {
                "ok": True,
                "channel": response["channel"],
                "ts": response["ts"]
            }
            
        except SlackApiError as e:
            error_msg = e.response["error"]
            logger.error(f"Slack API error (formatted): {error_msg}")
            
            return {
                "ok": False,
                "error": error_msg
            }
            
        except Exception as e:
            logger.error(f"Unexpected error (formatted): {e}")
            
            return {
                "ok": False,
                "error": str(e)
            }


# Global instance (initialized when bot token is available)
_slack_handler: Optional[SlackHandler] = None


def get_slack_handler(bot_token: str) -> SlackHandler:
    """
    Get or create the global Slack handler instance
    
    Uses singleton pattern - only one handler per app
    
    Args:
        bot_token: Your Slack bot token
        
    Returns:
        SlackHandler: The global Slack handler instance
    """
    global _slack_handler
    
    if _slack_handler is None:
        _slack_handler = SlackHandler(bot_token)
    
    return _slack_handler

