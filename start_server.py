#!/usr/bin/env python3
"""
Start script for Google Ads MCP Server on elast.io
"""
import os
import sys
import asyncio

def main():
    print("=== Starting Google Ads MCP Server ===")
    
    # Environment check
    required_vars = ["GOOGLE_PROJECT_ID", "GOOGLE_ADS_DEVELOPER_TOKEN"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"ERROR: Missing environment variables: {missing_vars}")
        sys.exit(1)
    
    print(f"Project ID: {os.environ.get('GOOGLE_PROJECT_ID')}")
    print(f"Developer Token: {'SET' if os.environ.get('GOOGLE_ADS_DEVELOPER_TOKEN') else 'NOT_SET'}")
    print(f"Credentials Base64: {'SET' if os.environ.get('GOOGLE_CREDENTIALS_BASE64') else 'NOT_SET'}")
    
    try:
        # Import and run MCP server
        from google_ads_mcp_server import mcp
        print("MCP server imported successfully")
        
        # Run with HTTP transport
        print("Starting HTTP server on port 7777...")
        mcp.run(transport="http", host="0.0.0.0", port=7777)
        
    except Exception as e:
        print(f"ERROR starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()