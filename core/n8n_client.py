"""
Relay - n8n API Client
Handles all interactions with n8n API for workflow management
built by Hak
"""

import logging
import httpx
from typing import Optional, List, Dict, Any
from config.settings import settings

logger = logging.getLogger(__name__)


class N8nClient:
    """
    n8n API Client for Relay

    Provides methods to:
    - List workflows
    - Get workflow details
    - Get executions (monitoring)
    - Activate/deactivate workflows
    - Create/modify workflows (future)
    """

    def __init__(self):
        """Initialize n8n client with API credentials"""
        if not settings.n8n_api_url or not settings.n8n_api_key:
            logger.warning("n8n API not configured - n8n features will not work")
            self.api_url = None
            self.api_key = None
            return

        # Store configuration
        self.api_url = settings.n8n_api_url.rstrip('/')  # Remove trailing slash
        self.api_key = settings.n8n_api_key

        # Create async HTTP client
        self.client = httpx.AsyncClient(
            timeout=30.0,  # 30 second timeout
            headers=self._get_headers()
        )

        logger.info(f"n8n client initialized for: {self.api_url}")

    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for n8n API requests

        n8n requires the API key in X-N8N-API-KEY header
        """
        return {
            "X-N8N-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def list_workflows(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all workflows from n8n

        Args:
            active_only: If True, only return active workflows

        Returns:
            List of workflow objects with id, name, active status, etc.
        """
        if not self.api_url:
            logger.error("n8n API not configured")
            return []

        try:
            url = f"{self.api_url}/workflows"
            response = await self.client.get(url)

            if response.status_code == 200:
                workflows = response.json()["data"]

                # Filter for active workflows if requested
                if active_only:
                    workflows = [w for w in workflows if w.get("active", False)]

                logger.info(f"Listed {len(workflows)} workflows" + (" (active only)" if active_only else ""))
                return workflows
            else:
                logger.error(f"Failed to list workflows: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error listing workflows: {e}")
            return []

    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details of a specific workflow

        Args:
            workflow_id: The workflow ID

        Returns:
            Workflow object with full details, or None if not found
        """
        if not self.api_url:
            logger.error("n8n API not configured")
            return None

        try:
            url = f"{self.api_url}/workflows/{workflow_id}"
            response = await self.client.get(url)

            if response.status_code == 200:
                workflow = response.json()["data"]
                logger.info(f"Retrieved workflow: {workflow.get('name', workflow_id)}")
                return workflow
            elif response.status_code == 404:
                logger.warning(f"Workflow {workflow_id} not found")
                return None
            else:
                logger.error(f"Failed to get workflow: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error getting workflow {workflow_id}: {e}")
            return None

    async def get_executions(
        self,
        workflow_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get workflow execution history

        Args:
            workflow_id: Optional - filter by specific workflow
            limit: Maximum number of executions to return (default 10)

        Returns:
            List of execution objects with status, start time, error details, etc.
        """
        if not self.api_url:
            logger.error("n8n API not configured")
            return []

        try:
            url = f"{self.api_url}/executions"
            params = {"limit": limit}

            # Only add workflowId if provided
            if workflow_id:
                params["workflowId"] = workflow_id

            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                executions = response.json()["data"]
                workflow_info = f" for workflow {workflow_id}" if workflow_id else ""
                logger.info(f"Retrieved {len(executions)} executions{workflow_info}")
                return executions
            else:
                logger.error(f"Failed to get executions: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error getting executions: {e}")
            return []

    async def activate_workflow(self, workflow_id: str) -> bool:
        """
        Activate a workflow (start monitoring triggers)

        Args:
            workflow_id: The workflow ID to activate

        Returns:
            True if successful, False otherwise
        """
        if not self.api_url:
            logger.error("n8n API not configured")
            return False

        try:
            url = f"{self.api_url}/workflows/{workflow_id}"
            response = await self.client.put(url, json={"active": True})

            if response.status_code == 200:
                logger.info(f"Activated workflow: {workflow_id}")
                return True
            else:
                logger.error(f"Failed to activate workflow: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error activating workflow {workflow_id}: {e}")
            return False

    async def deactivate_workflow(self, workflow_id: str) -> bool:
        """
        Deactivate a workflow (stop monitoring triggers)

        Args:
            workflow_id: The workflow ID to deactivate

        Returns:
            True if successful, False otherwise
        """
        if not self.api_url:
            logger.error("n8n API not configured")
            return False

        try:
            # Similar to activate_workflow but set active to False
            url = f"{self.api_url}/workflows/{workflow_id}"
            response = await self.client.put(url, json={"active": False})

            if response.status_code == 200:
                logger.info(f"Deactivated workflow: {workflow_id}")
                return True
            else:
                logger.error(f"Failed to deactivate workflow: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error deactivating workflow {workflow_id}: {e}")
            return False

    # =========================================================================
    # WORKFLOW OPERATIONS (create, delete, move, update)
    # =========================================================================

    async def create_workflow(self, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new workflow"""
        if not self.api_url:
            logger.error("n8n API not configured")
            return None

        try:
            url = f"{self.api_url}/workflows"
            response = await self.client.post(url, json=workflow_data)

            if response.status_code == 201:
                workflow = response.json()["data"]
                logger.info(f"Created workflow: {workflow.get('name', workflow.get('id'))}")
                return workflow
            else:
                logger.error(f"Failed to create workflow: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            return None

    async def update_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> bool:
        """Update an existing workflow"""
        if not self.api_url:
            logger.error("n8n API not configured")
            return False

        try:
            url = f"{self.api_url}/workflows/{workflow_id}"
            response = await self.client.put(url, json=workflow_data)

            if response.status_code == 200:
                logger.info(f"Updated workflow: {workflow_id}")
                return True
            else:
                logger.error(f"Failed to update workflow: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error updating workflow {workflow_id}: {e}")
            return False

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        if not self.api_url:
            logger.error("n8n API not configured")
            return False

        try:
            url = f"{self.api_url}/workflows/{workflow_id}"
            response = await self.client.delete(url)

            if response.status_code == 200:
                logger.info(f"Deleted workflow: {workflow_id}")
                return True
            else:
                logger.error(f"Failed to delete workflow: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error deleting workflow {workflow_id}: {e}")
            return False

    # =========================================================================
    # EXECUTION OPERATIONS (delete, retry)
    # =========================================================================

    async def delete_execution(self, execution_id: str) -> bool:
        """Delete an execution"""
        if not self.api_url:
            logger.error("n8n API not configured")
            return False

        try:
            url = f"{self.api_url}/executions/{execution_id}"
            response = await self.client.delete(url)

            if response.status_code == 200:
                logger.info(f"Deleted execution: {execution_id}")
                return True
            else:
                logger.error(f"Failed to delete execution: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error deleting execution {execution_id}: {e}")
            return False

    async def retry_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Retry a failed execution"""
        if not self.api_url:
            logger.error("n8n API not configured")
            return None

        try:
            url = f"{self.api_url}/executions/{execution_id}/retry"
            response = await self.client.post(url)

            if response.status_code == 200:
                execution = response.json()["data"]
                logger.info(f"Retried execution: {execution_id}")
                return execution
            else:
                logger.error(f"Failed to retry execution: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error retrying execution {execution_id}: {e}")
            return None

    # =========================================================================
    # CREDENTIAL OPERATIONS (create, delete)
    # =========================================================================

    async def create_credential(self, credential_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new credential"""
        if not self.api_url:
            logger.error("n8n API not configured")
            return None

        try:
            url = f"{self.api_url}/credentials"
            response = await self.client.post(url, json=credential_data)

            if response.status_code == 201:
                credential = response.json()["data"]
                logger.info(f"Created credential: {credential.get('name')}")
                return credential
            else:
                logger.error(f"Failed to create credential: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error creating credential: {e}")
            return None

    async def delete_credential(self, credential_id: str) -> bool:
        """Delete a credential"""
        if not self.api_url:
            logger.error("n8n API not configured")
            return False

        try:
            url = f"{self.api_url}/credentials/{credential_id}"
            response = await self.client.delete(url)

            if response.status_code == 200:
                logger.info(f"Deleted credential: {credential_id}")
                return True
            else:
                logger.error(f"Failed to delete credential: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error deleting credential {credential_id}: {e}")
            return False

    # =========================================================================
    # TAG OPERATIONS (create, delete, list, read, update)
    # =========================================================================

    async def list_tags(self) -> List[Dict[str, Any]]:
        """List all tags"""
        if not self.api_url:
            logger.error("n8n API not configured")
            return []

        try:
            url = f"{self.api_url}/tags"
            response = await self.client.get(url)

            if response.status_code == 200:
                tags = response.json()["data"]
                logger.info(f"Listed {len(tags)} tags")
                return tags
            else:
                logger.error(f"Failed to list tags: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error listing tags: {e}")
            return []

    async def create_tag(self, tag_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new tag"""
        if not self.api_url:
            logger.error("n8n API not configured")
            return None

        try:
            url = f"{self.api_url}/tags"
            response = await self.client.post(url, json=tag_data)

            if response.status_code == 201:
                tag = response.json()["data"]
                logger.info(f"Created tag: {tag.get('name')}")
                return tag
            else:
                logger.error(f"Failed to create tag: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error creating tag: {e}")
            return None

    async def delete_tag(self, tag_id: str) -> bool:
        """Delete a tag"""
        if not self.api_url:
            logger.error("n8n API not configured")
            return False

        try:
            url = f"{self.api_url}/tags/{tag_id}"
            response = await self.client.delete(url)

            if response.status_code == 200:
                logger.info(f"Deleted tag: {tag_id}")
                return True
            else:
                logger.error(f"Failed to delete tag: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error deleting tag {tag_id}: {e}")
            return False

    # =========================================================================
    # VARIABLE OPERATIONS (create, delete, list, update)
    # =========================================================================

    async def list_variables(self) -> List[Dict[str, Any]]:
        """List all environment variables"""
        if not self.api_url:
            logger.error("n8n API not configured")
            return []

        try:
            url = f"{self.api_url}/variables"
            response = await self.client.get(url)

            if response.status_code == 200:
                variables = response.json()["data"]
                logger.info(f"Listed {len(variables)} variables")
                return variables
            else:
                logger.error(f"Failed to list variables: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error listing variables: {e}")
            return []

    async def create_variable(self, variable_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new environment variable"""
        if not self.api_url:
            logger.error("n8n API not configured")
            return None

        try:
            url = f"{self.api_url}/variables"
            response = await self.client.post(url, json=variable_data)

            if response.status_code == 201:
                variable = response.json()["data"]
                logger.info(f"Created variable: {variable.get('key')}")
                return variable
            else:
                logger.error(f"Failed to create variable: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error creating variable: {e}")
            return None

    async def delete_variable(self, variable_id: str) -> bool:
        """Delete an environment variable"""
        if not self.api_url:
            logger.error("n8n API not configured")
            return False

        try:
            url = f"{self.api_url}/variables/{variable_id}"
            response = await self.client.delete(url)

            if response.status_code == 200:
                logger.info(f"Deleted variable: {variable_id}")
                return True
            else:
                logger.error(f"Failed to delete variable: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error deleting variable {variable_id}: {e}")
            return False

    async def close(self):
        """Close the HTTP client (cleanup)"""
        if hasattr(self, 'client'):
            await self.client.aclose()
            logger.info("n8n client closed")


# Create a single global instance
# Import this everywhere: from core.n8n_client import n8n_client
n8n_client = N8nClient()
