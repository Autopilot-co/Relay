"""
Relay - Memory & Persistence System
Handles saving/loading conversation history and workflow metadata
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from utils.logger import logger


class Memory:
    """
    Simple file-based persistence for Relay

    Saves:
    - Conversation history per channel
    - Workflow metadata (what Relay built)
    """

    def __init__(self, data_dir: str = "data"):
        """Initialize memory system with data directory"""
        self.data_dir = Path(data_dir)
        self.conversations_dir = self.data_dir / "conversations"
        self.workflows_file = self.data_dir / "workflows_built.json"

        # Create directories if they don't exist
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Memory system initialized at: {self.data_dir}")

    # =========================================================================
    # CONVERSATION HISTORY
    # =========================================================================

    def save_conversation(self, conv_key: str, messages: List[Dict[str, str]]) -> bool:
        """
        Save conversation history to file

        Args:
            conv_key: Conversation identifier (e.g., "channel_C123:main")
            messages: List of message dicts [{"role": "user", "content": "..."}]

        Returns:
            True if saved successfully
        """
        try:
            # Sanitize filename (replace : with _)
            filename = conv_key.replace(":", "_").replace("/", "_") + ".json"
            filepath = self.conversations_dir / filename

            # Save with metadata
            data = {
                "conv_key": conv_key,
                "last_updated": datetime.now().isoformat(),
                "message_count": len(messages),
                "messages": messages
            }

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved conversation: {conv_key} ({len(messages)} messages)")
            return True

        except Exception as e:
            logger.error(f"Error saving conversation {conv_key}: {e}")
            return False

    def load_conversation(self, conv_key: str) -> List[Dict[str, str]]:
        """
        Load conversation history from file

        Args:
            conv_key: Conversation identifier

        Returns:
            List of messages, or empty list if not found
        """
        try:
            filename = conv_key.replace(":", "_").replace("/", "_") + ".json"
            filepath = self.conversations_dir / filename

            if not filepath.exists():
                return []

            with open(filepath, 'r') as f:
                data = json.load(f)

            messages = data.get("messages", [])
            logger.debug(f"Loaded conversation: {conv_key} ({len(messages)} messages)")
            return messages

        except Exception as e:
            logger.error(f"Error loading conversation {conv_key}: {e}")
            return []

    def delete_conversation(self, conv_key: str) -> bool:
        """Delete a conversation history file"""
        try:
            filename = conv_key.replace(":", "_").replace("/", "_") + ".json"
            filepath = self.conversations_dir / filename

            if filepath.exists():
                filepath.unlink()
                logger.info(f"Deleted conversation: {conv_key}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error deleting conversation {conv_key}: {e}")
            return False

    def list_conversations(self) -> List[str]:
        """List all saved conversation keys"""
        try:
            conversations = []
            for filepath in self.conversations_dir.glob("*.json"):
                # Convert filename back to conv_key
                conv_key = filepath.stem.replace("_", ":", 1)  # Replace first _ with :
                conversations.append(conv_key)

            return conversations

        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            return []

    # =========================================================================
    # WORKFLOW METADATA
    # =========================================================================

    def save_workflow_built(
        self,
        workflow_id: str,
        workflow_name: str,
        description: str,
        channel: str,
        user: str
    ) -> bool:
        """
        Save metadata about a workflow Relay built

        Args:
            workflow_id: n8n workflow ID
            workflow_name: Name of the workflow
            description: What the workflow does
            channel: Slack channel it was built in
            user: User who requested it

        Returns:
            True if saved successfully
        """
        try:
            # Load existing workflows
            workflows = self._load_workflows_data()

            # Add new workflow
            workflows.append({
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "description": description,
                "channel": channel,
                "user": user,
                "created_at": datetime.now().isoformat()
            })

            # Save back
            with open(self.workflows_file, 'w') as f:
                json.dump(workflows, f, indent=2)

            logger.info(f"Saved workflow metadata: {workflow_name} (ID: {workflow_id})")
            return True

        except Exception as e:
            logger.error(f"Error saving workflow metadata: {e}")
            return False

    def get_workflows_built(self, channel: Optional[str] = None) -> List[Dict]:
        """
        Get list of workflows Relay built

        Args:
            channel: Optional - filter by Slack channel

        Returns:
            List of workflow metadata dicts
        """
        try:
            workflows = self._load_workflows_data()

            if channel:
                workflows = [w for w in workflows if w.get("channel") == channel]

            return workflows

        except Exception as e:
            logger.error(f"Error getting workflows: {e}")
            return []

    def _load_workflows_data(self) -> List[Dict]:
        """Internal: Load workflows data file"""
        try:
            if not self.workflows_file.exists():
                return []

            with open(self.workflows_file, 'r') as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Error loading workflows data: {e}")
            return []


# Create global instance
memory = Memory()
