#!/usr/bin/env python3
"""
HTTP wrapper for Google Ads MCP Server
Provides a simple HTTP API to interact with the MCP server
"""

import json
import subprocess
import sys
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "google-ads-mcp-wrapper"})

@app.route('/mcp', methods=['POST'])
def mcp_proxy():
    """Proxy requests to MCP server"""
    try:
        # Get JSON request from client
        mcp_request = request.get_json()
        
        if not mcp_request:
            return jsonify({"error": "No JSON payload provided"}), 400
        
        # Start MCP server process
        process = subprocess.Popen(
            [sys.executable, '-m', 'ads_mcp.server'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send request to MCP server
        stdout, stderr = process.communicate(
            input=json.dumps(mcp_request) + '\n',
            timeout=30
        )
        
        if process.returncode != 0:
            app.logger.error(f"MCP server error: {stderr}")
            return jsonify({"error": "MCP server error", "details": stderr}), 500
        
        # Parse response
        try:
            response = json.loads(stdout.strip())
            return jsonify(response)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON response from MCP server", "raw_output": stdout}), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({"error": "MCP server timeout"}), 504
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/tools', methods=['GET'])
def list_tools():
    """List available MCP tools"""
    try:
        # Initialize request to get tool list
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        process = subprocess.Popen(
            [sys.executable, '-m', 'ads_mcp.server'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(
            input=json.dumps(init_request) + '\n',
            timeout=30
        )
        
        if process.returncode != 0:
            return jsonify({"error": "Failed to get tools", "details": stderr}), 500
            
        try:
            response = json.loads(stdout.strip())
            return jsonify(response)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid response", "raw_output": stdout}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API documentation"""
    return jsonify({
        "service": "Google Ads MCP HTTP Wrapper",
        "endpoints": {
            "/health": "Health check",
            "/tools": "List available MCP tools",
            "/mcp": "POST - Proxy requests to MCP server"
        },
        "usage": {
            "mcp_request_format": {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "search",
                    "arguments": {
                        "customer_id": "123-456-7890",
                        "query": "SELECT campaign.name FROM campaign"
                    }
                }
            }
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
