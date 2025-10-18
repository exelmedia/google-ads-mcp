#!/usr/bin/env python3

"""FastMCP server wrapper for Google Ads MCP."""

import os
from fastmcp import FastMCP

# Initialize FastMCP
mcp = FastMCP("Google Ads MCP")

# Import tools to register them
from ads_mcp.tools import search, core

# For HTTP transport
if __name__ == "__main__":
    # Run the server
    mcp.run()