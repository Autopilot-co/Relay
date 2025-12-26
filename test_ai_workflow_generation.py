"""
Test Script: Can AI Generate Valid n8n Workflows?

This script tests if gpt-oss-120b can generate valid n8n workflow JSON
from an example workflow.
"""

import os
import json
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Example n8n workflow (simple HTTP check)
EXAMPLE_WORKFLOW = {
    "name": "Simple API Check",
    "nodes": [
        {
            "id": "1",
            "name": "Schedule",
            "type": "n8n-nodes-base.cron",
            "typeVersion": 1,
            "position": [250, 300],
            "parameters": {
                "triggerTimes": {
                    "item": [{"hour": 9, "minute": 0}]
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
                "url": "https://api.example.com/status"
            }
        }
    ],
    "connections": {
        "Schedule": {
            "main": [[{"node": "Check API", "type": "main", "index": 0}]]
        }
    },
    "active": False
}


async def test_workflow_generation():
    """Test if AI can generate a valid n8n workflow from an example"""

    print("=" * 80)
    print("🧪 TESTING: Can AI Generate Valid n8n Workflows?")
    print("=" * 80)
    print()

    # Check if API key is set
    api_key = os.environ.get("CEREBRAS_API_KEY")
    if not api_key:
        print("❌ ERROR: CEREBRAS_API_KEY not set in environment")
        print("Please set it in your .env file or export it:")
        print("export CEREBRAS_API_KEY=your-key-here")
        return

    # Initialize Cerebras client
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.cerebras.ai/v1"
    )

    # Create the prompt
    prompt = f"""You are an expert in n8n workflow automation.

Here is an example of a REAL working n8n workflow:

{json.dumps(EXAMPLE_WORKFLOW, indent=2)}

Now, create a SIMILAR n8n workflow with these requirements:
- Name: "Weather Forecast Check"
- Runs daily at 2 PM (14:00)
- Makes HTTP GET request to: https://api.weather.com/forecast
- Follow the EXACT same JSON structure as the example
- Use the EXACT same node type format (n8n-nodes-base.{type})
- Use the EXACT same connection structure

Return ONLY the valid JSON workflow, no explanations."""

    print("📝 PROMPT:")
    print("-" * 80)
    print(prompt)
    print()
    print("=" * 80)
    print("🤖 SENDING TO GPT-OSS-120B...")
    print("=" * 80)
    print()

    try:
        # Call AI
        response = await client.chat.completions.create(
            model="gpt-oss-120b",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent output
            max_completion_tokens=2000
        )

        ai_output = response.choices[0].message.content

        print("✅ AI RESPONSE:")
        print("-" * 80)
        print(ai_output)
        print()
        print("=" * 80)
        print()

        # Try to parse as JSON
        print("🔍 VALIDATING JSON...")
        print("-" * 80)

        try:
            # Extract JSON if wrapped in markdown code blocks
            if "```json" in ai_output:
                json_str = ai_output.split("```json")[1].split("```")[0].strip()
            elif "```" in ai_output:
                json_str = ai_output.split("```")[1].split("```")[0].strip()
            else:
                json_str = ai_output.strip()

            workflow = json.loads(json_str)

            print("✅ VALID JSON!")
            print()
            print("📊 ANALYSIS:")
            print("-" * 80)
            print(f"✅ Workflow name: {workflow.get('name')}")
            print(f"✅ Number of nodes: {len(workflow.get('nodes', []))}")
            print(f"✅ Has connections: {bool(workflow.get('connections'))}")
            print()

            # Check node types
            print("📦 NODES:")
            for node in workflow.get('nodes', []):
                print(f"  - {node.get('name')}: {node.get('type')}")
            print()

            # Check if it followed the structure
            print("🎯 STRUCTURE VALIDATION:")
            has_cron = any('cron' in node.get('type', '') for node in workflow.get('nodes', []))
            has_http = any('http' in node.get('type', '').lower() for node in workflow.get('nodes', []))

            print(f"  {'✅' if has_cron else '❌'} Has cron/schedule node")
            print(f"  {'✅' if has_http else '❌'} Has HTTP request node")
            print(f"  {'✅' if workflow.get('connections') else '❌'} Has connections defined")
            print()

            # Save to file
            output_file = "test_generated_workflow.json"
            with open(output_file, 'w') as f:
                json.dump(workflow, f, indent=2)

            print(f"💾 Saved generated workflow to: {output_file}")
            print()
            print("=" * 80)
            print("🎉 TEST COMPLETE!")
            print("=" * 80)
            print()
            print("Next steps:")
            print("1. Review the generated workflow JSON")
            print("2. Try importing it into your n8n instance")
            print("3. See if n8n accepts it!")

        except json.JSONDecodeError as e:
            print(f"❌ INVALID JSON: {e}")
            print()
            print("The AI didn't return valid JSON. This could mean:")
            print("- It added explanatory text around the JSON")
            print("- The JSON has syntax errors")
            print("- The AI needs better examples")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        print()
        print("Something went wrong calling the Cerebras API.")

    finally:
        await client.close()


if __name__ == "__main__":
    print()
    asyncio.run(test_workflow_generation())
    print()
