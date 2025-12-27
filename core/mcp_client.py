"""
Relay - MCP (Model Context Protocol) Client
Connects Relay to n8n (and other platforms) via standardized MCP protocol

MCP Architecture:
- Host: Relay (this application)
- Client: This file (MCPClient class)
- Server: n8n MCP server (czlonkowski/n8n-mcp)
- Protocol: JSON-RPC 2.0

References:
- MCP Spec: https://modelcontextprotocol.io/specification/2025-11-25
- n8n MCP: https://github.com/czlonkowski/n8n-mcp
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """Represents an MCP tool (function AI can call)"""
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class MCPResource:
    """Represents an MCP resource (data AI can read)"""
    uri: str
    name: str
    description: str
    mime_type: str


class MCPClient:
    """
    MCP Client for connecting to MCP servers (n8n, Zapier, Make, etc.)

    Implements JSON-RPC 2.0 protocol for standardized AI-to-tool communication
    """

    def __init__(self, server_url: str, server_name: str = "default"):
        """
        Initialize MCP client

        Args:
            server_url: URL of the MCP server (e.g., http://localhost:3000/mcp)
            server_name: Name identifier for this server connection
        """
        self.server_url = server_url
        self.server_name = server_name
        self.protocol_version = "2025-06-18"  # Latest MCP spec version
        self.session_id = None
        self.tools: List[MCPTool] = []
        self.resources: List[MCPResource] = []
        self.initialized = False

        logger.info(f"MCP Client created for {server_name} at {server_url}")

    async def initialize(self) -> bool:
        """
        Initialize connection to MCP server (handshake)

        Returns:
            True if initialization successful
        """
        try:
            # Send initialize request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": self.protocol_version,
                    "capabilities": {
                        "tools": True,
                        "resources": True,
                        "prompts": True
                    },
                    "clientInfo": {
                        "name": "Relay",
                        "version": "1.0.0"
                    }
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.server_url,
                    json=request,
                    timeout=30.0
                )

                if response.status_code != 200:
                    logger.error(f"MCP initialization failed: {response.status_code}")
                    return False

                result = response.json()

                if "error" in result:
                    logger.error(f"MCP error: {result['error']}")
                    return False

                # Parse server capabilities
                server_info = result.get("result", {})
                logger.info(f"MCP server info: {server_info.get('serverInfo', {})}")

                # Request available tools
                await self._discover_tools()

                # Request available resources
                await self._discover_resources()

                self.initialized = True
                logger.info(f"MCP initialized: {len(self.tools)} tools, {len(self.resources)} resources")

                return True

        except Exception as e:
            logger.error(f"MCP initialization error: {e}")
            return False

    async def _discover_tools(self):
        """Discover available tools from MCP server"""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(self.server_url, json=request, timeout=30.0)
                result = response.json()

                if "result" in result and "tools" in result["result"]:
                    for tool_data in result["result"]["tools"]:
                        tool = MCPTool(
                            name=tool_data["name"],
                            description=tool_data.get("description", ""),
                            input_schema=tool_data.get("inputSchema", {})
                        )
                        self.tools.append(tool)

                    logger.info(f"Discovered {len(self.tools)} tools")

        except Exception as e:
            logger.error(f"Error discovering tools: {e}")

    async def _discover_resources(self):
        """Discover available resources from MCP server"""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "resources/list"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(self.server_url, json=request, timeout=30.0)
                result = response.json()

                if "result" in result and "resources" in result["result"]:
                    for res_data in result["result"]["resources"]:
                        resource = MCPResource(
                            uri=res_data["uri"],
                            name=res_data.get("name", ""),
                            description=res_data.get("description", ""),
                            mime_type=res_data.get("mimeType", "application/json")
                        )
                        self.resources.append(resource)

                    logger.info(f"Discovered {len(self.resources)} resources")

        except Exception as e:
            logger.error(f"Error discovering resources: {e}")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool (e.g., create_workflow, list_workflows)

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result
        """
        if not self.initialized:
            await self.initialize()

        try:
            request = {
                "jsonrpc": "2.0",
                "id": None,  # Will be assigned
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.server_url,
                    json=request,
                    timeout=120.0  # Longer timeout for tool execution
                )

                result = response.json()

                if "error" in result:
                    logger.error(f"Tool call error: {result['error']}")
                    return {"error": result["error"]}

                return result.get("result", {})

        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {"error": str(e)}

    async def read_resource(self, resource_uri: str) -> Any:
        """
        Read an MCP resource (e.g., n8n://workflows)

        Args:
            resource_uri: URI of the resource to read

        Returns:
            Resource data
        """
        if not self.initialized:
            await self.initialize()

        try:
            request = {
                "jsonrpc": "2.0",
                "id": None,
                "method": "resources/read",
                "params": {
                    "uri": resource_uri
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(self.server_url, json=request, timeout=30.0)
                result = response.json()

                if "error" in result:
                    logger.error(f"Resource read error: {result['error']}")
                    return None

                return result.get("result", {})

        except Exception as e:
            logger.error(f"Error reading resource {resource_uri}: {e}")
            return None

    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        Get tools formatted for LLM function calling

        Returns:
            List of tool definitions in OpenAI function calling format
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": f"{self.server_name}_{tool.name}",
                    "description": tool.description,
                    "parameters": tool.input_schema
                }
            }
            for tool in self.tools
        ]

    def get_available_tools_description(self) -> str:
        """
        Get human-readable description of available tools

        Returns:
            Formatted string describing all tools
        """
        if not self.tools:
            return f"No tools available from {self.server_name}"

        descriptions = [f"\n**{self.server_name} Tools:**"]
        for tool in self.tools:
            descriptions.append(f"  • {tool.name}: {tool.description}")

        return "\n".join(descriptions)


class MCPManager:
    """
    Manages multiple MCP clients (n8n, Zapier, Make, etc.)

    Allows Relay to connect to multiple platforms simultaneously
    """

    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
        logger.info("MCP Manager initialized")

    async def add_server(self, name: str, url: str) -> bool:
        """
        Add an MCP server connection

        Args:
            name: Server identifier (e.g., "n8n", "zapier")
            url: MCP server URL

        Returns:
            True if connection successful
        """
        try:
            client = MCPClient(server_url=url, server_name=name)
            success = await client.initialize()

            if success:
                self.clients[name] = client
                logger.info(f"Added MCP server: {name}")
                return True
            else:
                logger.error(f"Failed to add MCP server: {name}")
                return False

        except Exception as e:
            logger.error(f"Error adding MCP server {name}: {e}")
            return False

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on a specific MCP server

        Args:
            server_name: Which server to call (e.g., "n8n")
            tool_name: Tool to execute
            arguments: Tool arguments

        Returns:
            Tool result
        """
        if server_name not in self.clients:
            return {"error": f"Server {server_name} not connected"}

        client = self.clients[server_name]
        return await client.call_tool(tool_name, arguments)

    def get_all_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Get all tools from all servers formatted for LLM"""
        all_tools = []
        for client in self.clients.values():
            all_tools.extend(client.get_tools_for_llm())
        return all_tools

    def get_tools_description(self) -> str:
        """Get human-readable description of all available tools"""
        descriptions = []
        for client in self.clients.values():
            descriptions.append(client.get_available_tools_description())
        return "\n".join(descriptions)


# Global MCP manager instance
mcp_manager = MCPManager()
