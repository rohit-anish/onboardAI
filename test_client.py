import asyncio
import json
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_mcp_client_test():
    repo_path = Path(__file__).parent.resolve()
    print(f"Connecting to OnboardAI MCP Server locally...")
    
    server_params = StdioServerParameters(
        command="python",
        args=[str(repo_path / "main.py"), "--mode", "stdio"]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 1. Initialize the connection
                await session.initialize()
                print("✓ Successfully connected and initialized MCP session!")
                
                # 2. List the available tools
                tools_result = await session.list_tools()
                print("\n--- Available Tools Exposed by Server ---")
                for tool in tools_result.tools:
                    print(f"- {tool.name}: {tool.description}")
                
                # 3. Call the onboarding plan tool
                print("\n--- Calling Tool: 'generate_onboarding_plan' ---")
                plan_response = await session.call_tool(
                    "generate_onboarding_plan",
                    arguments={
                        "repo_path": str(repo_path),
                        "role": "New Engineer",
                        "target_module": "GraphifyAdapter"
                    }
                )
                
                # Print response content
                if plan_response.content:
                    text_content = plan_response.content[0].text
                    # The response is returned as a JSON string or dict depending on the return type
                    try:
                        parsed = json.loads(text_content)
                        print(json.dumps(parsed, indent=2))
                    except Exception:
                        print(text_content)
                else:
                    print("No content returned.")
                    
                # 4. Call the Q&A tool
                print("\n--- Calling Tool: 'ask_repository_question' ---")
                qa_response = await session.call_tool(
                    "ask_repository_question",
                    arguments={
                        "repo_path": str(repo_path),
                        "question": "How does the project work?",
                        "work_context": "Creating a visual mindmap generator"
                    }
                )
                
                if qa_response.content:
                    print(qa_response.content[0].text)
                else:
                    print("No content returned.")

    except Exception as e:
        print(f"\nError running MCP client test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Fix event loop policy for Windows if needed
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(run_mcp_client_test())
