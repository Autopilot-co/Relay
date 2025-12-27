"""
Test MCP Connection
Tests that Relay can connect to n8n MCP server and discover tools
"""

import asyncio
import logging
from config.settings import settings
from core.mcp_client import mcp_manager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mcp_connection():
    """Test MCP connection and tool discovery"""

    print("\n" + "=" * 60)
    print("MCP CONNECTION TEST")
    print("=" * 60 + "\n")

    # Check configuration
    if not settings.n8n_mcp_url:
        print("❌ ERROR: N8N_MCP_URL not set in .env file")
        print("\nPlease add to your .env file:")
        print("N8N_MCP_URL=http://localhost:3000/mcp")
        return False

    print(f"📡 Connecting to n8n MCP server: {settings.n8n_mcp_url}")
    print()

    # Try to connect
    try:
        success = await mcp_manager.add_server("n8n", settings.n8n_mcp_url)

        if not success:
            print("❌ Failed to connect to MCP server")
            print("\nTroubleshooting:")
            print("1. Is the n8n MCP server running?")
            print("   Run: npx @modelcontextprotocol/server-n8n --api-key YOUR_KEY --base-url YOUR_N8N_URL")
            print("2. Is the URL correct in .env?")
            print("3. Check the logs above for errors")
            return False

        print("✅ Successfully connected to n8n MCP server!")
        print()

        # Get the client
        client = mcp_manager.clients.get("n8n")

        if not client:
            print("❌ Client not found after connection")
            return False

        # Display discovered tools
        print(f"🔧 Discovered {len(client.tools)} tools:")
        print()

        for i, tool in enumerate(client.tools[:10], 1):  # Show first 10
            print(f"  {i}. {tool.name}")
            print(f"     {tool.description}")
            print()

        if len(client.tools) > 10:
            print(f"  ... and {len(client.tools) - 10} more tools")
            print()

        # Display discovered resources
        print(f"📚 Discovered {len(client.resources)} resources")
        if client.resources:
            for resource in client.resources[:5]:
                print(f"  • {resource.name}: {resource.uri}")

        print()
        print("=" * 60)
        print("✅ MCP CONNECTION TEST PASSED")
        print("=" * 60)
        print()

        return True

    except Exception as e:
        print(f"❌ Error during connection: {e}")
        logger.exception("Connection error details:")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_mcp_connection())

    if result:
        print("🎉 MCP is ready to use!")
        print("\nNext steps:")
        print("1. Start the Relay server: python main.py")
        print("2. Test via Slack or API")
    else:
        print("❌ MCP connection failed")
        print("\nSee troubleshooting steps above")
