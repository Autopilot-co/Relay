"""
Relay - Slack Webhook Handler
Receives events from Slack (messages, mentions, etc.)

Production-ready features:
- Challenge verification (Slack setup requirement)
- Signature verification (security)
- Async processing (fast responses)
- Proper error handling
- Conversation history tracking
"""

import hmac
import hashlib
import time
from fastapi import Request, HTTPException
from utils.logger import logger
from platforms.slack_handler import get_slack_handler
from typing import Optional, Dict, List

# In-memory conversation storage
# Key: f"{channel}:{thread_ts}" (thread_ts for threaded convos, or message ts for new threads)
# Value: List of message dicts [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
conversation_history: Dict[str, List[Dict[str, str]]] = {}


async def verify_slack_signature(request: Request, signing_secret: str) -> bool:
    """
    Verify that the request actually came from Slack (not a hacker)
    
    How it works:
    1. Slack signs every request with a secret key
    2. We compute the same signature on our end
    3. If they match = legitimate request from Slack
    4. If they don't = someone is pretending to be Slack
    
    Args:
        request: The incoming FastAPI request
        signing_secret: Your Slack app's signing secret
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    
    # Get Slack's signature from request headers
    slack_signature = request.headers.get("X-Slack-Signature", "")
    slack_timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    
    # Security: Reject old requests (prevents replay attacks)
    # If request is more than 5 minutes old, reject it
    if abs(time.time() - int(slack_timestamp)) > 60 * 5:
        logger.warning("Request timestamp too old, possible replay attack")
        return False
    
    # Get the raw request body
    body = await request.body()
    
    # Compute the signature (same way Slack does)
    # Format: v0:timestamp:body
    sig_basestring = f"v0:{slack_timestamp}:{body.decode('utf-8')}"
    
    # Use HMAC-SHA256 to compute signature
    my_signature = 'v0=' + hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures (secure comparison to prevent timing attacks)
    is_valid = hmac.compare_digest(my_signature, slack_signature)
    
    if not is_valid:
        logger.warning("Invalid Slack signature!")
    
    return is_valid


async def handle_slack_webhook(
    request: Request, 
    signing_secret: str,
    bot_token: Optional[str] = None
) -> dict:
    """
    Main handler for Slack webhook events
    
    Handles:
    1. Challenge verification (one-time Slack setup)
    2. Message events (when users send messages)
    3. Other events (mentions, reactions, etc.)
    
    Args:
        request: The incoming FastAPI request
        signing_secret: Your Slack app's signing secret
        bot_token: Your Slack bot token (for sending responses)
        
    Returns:
        dict: Response to send back to Slack
    """
    
    # SECURITY: Verify the request is really from Slack
    if signing_secret:  # Only verify if secret is configured
        is_valid = await verify_slack_signature(request, signing_secret)
        if not is_valid:
            logger.error("Invalid Slack signature, rejecting request")
            raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Parse the JSON payload from Slack
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse Slack request: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Log what we received (helpful for debugging)
    logger.info(f"Received Slack event: {data.get('type', 'unknown')}")
    
    # -------------------------------------------------------------------------
    # STEP 1: Handle Challenge Verification (one-time setup)
    # -------------------------------------------------------------------------
    # When you first configure the webhook URL in Slack, Slack sends a challenge
    # We must echo it back to prove we own this endpoint
    
    if data.get("type") == "url_verification":
        challenge = data.get("challenge", "")
        logger.info(f"Challenge verification received: {challenge}")
        return {"challenge": challenge}
    
    # -------------------------------------------------------------------------
    # STEP 2: Handle Event Callbacks (actual messages)
    # -------------------------------------------------------------------------
    # This is where real user messages come through
    
    if data.get("type") == "event_callback":
        event = data.get("event", {})
        event_type = event.get("type", "")
        
        # Handle message events
        if event_type == "message":
            # Extract message details
            user = event.get("user", "unknown")
            text = event.get("text", "")
            channel = event.get("channel", "")
            ts = event.get("ts", "")  # timestamp (message ID)
            
            # Ignore bot messages (prevent infinite loops!)
            if event.get("bot_id"):
                logger.debug("Ignoring bot message")
                return {"ok": True}
            
            # Ignore message subtypes (edits, deletes, etc.)
            if event.get("subtype"):
                logger.debug(f"Ignoring message subtype: {event.get('subtype')}")
                return {"ok": True}
            
            # Log the message
            logger.info(f"Message from user {user} in channel {channel}: {text}")
            
            # ----------------------------------------------------------------
            # AI-POWERED RESPONSES: Use Relay AI engine with conversation memory
            # ----------------------------------------------------------------

            if bot_token:
                try:
                    # Get Slack handler and AI engine
                    slack = get_slack_handler(bot_token)
                    from core.ai_engine import ai_engine

                    # Create conversation key (channel + thread)
                    # Use thread_ts if in a thread, otherwise start new thread with this message
                    thread_id = event.get("thread_ts", ts)
                    conv_key = f"{channel}:{thread_id}"

                    # Get existing conversation history
                    history = conversation_history.get(conv_key, [])

                    # Process message with AI (includes conversation context)
                    ai_response = await ai_engine.process_message(text, conversation_history=history)

                    # Update conversation history
                    history.append({"role": "user", "content": text})
                    history.append({"role": "assistant", "content": ai_response})
                    conversation_history[conv_key] = history

                    # Keep only last 20 messages (10 exchanges) to avoid token limits
                    if len(conversation_history[conv_key]) > 20:
                        conversation_history[conv_key] = conversation_history[conv_key][-20:]

                    # Send AI response back to Slack (in main channel)
                    await slack.send_message(
                        channel=channel,
                        text=ai_response
                        # No thread_ts = reply in main channel like Discord
                    )

                    logger.info(f"AI response sent successfully (conv_key: {conv_key}, history: {len(history)} messages)")

                except Exception as e:
                    logger.error(f"Failed to send AI response: {e}")
            else:
                logger.warning("Bot token not configured, cannot send response")
            
            return {"ok": True}
        
        # Handle app mentions (@bot)
        elif event_type == "app_mention":
            user = event.get("user", "unknown")
            text = event.get("text", "")
            channel = event.get("channel", "")
            ts = event.get("ts", "")
            
            logger.info(f"Mentioned by user {user} in channel {channel}: {text}")
            
            # ----------------------------------------------------------------
            # MENTION RESPONSE: Bot was @mentioned - use AI with conversation memory
            # ----------------------------------------------------------------

            if bot_token:
                try:
                    slack = get_slack_handler(bot_token)
                    from core.ai_engine import ai_engine

                    # Create conversation key (use channel since we're not threading)
                    conv_key = f"{channel}:main"

                    # Get existing conversation history
                    history = conversation_history.get(conv_key, [])

                    # Process mention with AI
                    ai_response = await ai_engine.process_message(text, conversation_history=history)

                    # Update conversation history
                    history.append({"role": "user", "content": text})
                    history.append({"role": "assistant", "content": ai_response})
                    conversation_history[conv_key] = history

                    # Keep only last 20 messages
                    if len(conversation_history[conv_key]) > 20:
                        conversation_history[conv_key] = conversation_history[conv_key][-20:]

                    await slack.send_message(
                        channel=channel,
                        text=ai_response
                        # No thread_ts = reply in main channel
                    )

                    logger.info(f"Mention response sent successfully (conv_key: {conv_key}, history: {len(history)} messages)")

                except Exception as e:
                    logger.error(f"Failed to send mention response: {e}")
            
            return {"ok": True}
        
        # Handle other events
        else:
            logger.debug(f"Unhandled event type: {event_type}")
            return {"ok": True}
    
    # -------------------------------------------------------------------------
    # STEP 3: Handle Unknown Event Types
    # -------------------------------------------------------------------------
    logger.warning(f"Unknown Slack event type: {data.get('type')}")
    return {"ok": True}

