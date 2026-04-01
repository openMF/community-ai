import sys
import os

# Add the parent directory to sys.path so we can import modules correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from MCP_Enhancement.tools.mifos_tools import mcp

if __name__ == "__main__":
    print("🚀 Starting MCP Inspector Runner for Mifos Agent...")
    # Run the server using stdio for the inspector to connect
    mcp.run(transport="stdio")