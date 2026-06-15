import argparse
import os
import sys

# Ensure current directory is in sys.path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_server.server import mcp

def main():
    parser = argparse.ArgumentParser(description="OnboardAI MCP Server")
    parser.add_argument(
        "--mode", 
        choices=["stdio", "sse"], 
        default="stdio", 
        help="MCP server transport mode (stdio or sse)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port for SSE server (default: 8000)"
    )
    parser.add_argument(
        "--host", 
        default="127.0.0.1", 
        help="Host for SSE server (default: 127.0.0.1)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "stdio":
        print("Starting OnboardAI MCP Server in STDIO mode...", file=sys.stderr)
        mcp.run(transport="stdio")
    elif args.mode == "sse":
        print(f"Starting OnboardAI MCP Server in SSE mode on http://{args.host}:{args.port}", file=sys.stderr)
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="sse")

if __name__ == "__main__":
    main()
