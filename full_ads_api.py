#!/usr/bin/env python3
"""
Full Google Ads API - HTTP endpoints for all Google Ads MCP tools
Based on successful GA MCP API implementation
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import uvicorn
import os
from typing import Optional, List, AsyncIterator
import json
import base64
import asyncio
from dotenv import load_dotenv

# Try to load from .env file
load_dotenv()

# DEBUG: Print environment variables at startup
print("=== DEBUG: Environment Variables ===")
print(f"GOOGLE_PROJECT_ID: {os.environ.get('GOOGLE_PROJECT_ID', 'NOT_SET')}")
print(f"GOOGLE_ADS_DEVELOPER_TOKEN: {'***' if os.environ.get('GOOGLE_ADS_DEVELOPER_TOKEN') else 'NOT_SET'}")
print(f"GOOGLE_CREDENTIALS_BASE64 length: {len(os.environ.get('GOOGLE_CREDENTIALS_BASE64', ''))}")
print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'NOT_SET')}")
print("=====================================")

# Function to setup credentials from Base64
def setup_credentials():
    """Setup Google credentials from Base64 environment variable"""
    print("=== DEBUG: setup_credentials() called ===")
    try:
        credentials_base64 = os.environ.get('GOOGLE_CREDENTIALS_BASE64')
        print(f"credentials_base64 length: {len(credentials_base64) if credentials_base64 else 0}")
        if not credentials_base64:
            print("ERROR: GOOGLE_CREDENTIALS_BASE64 not found in environment")
            return False, "GOOGLE_CREDENTIALS_BASE64 not set"
        
        # Use project directory for credentials
        project_dir = '/opt/app/google-ads-mcp'
        os.makedirs(project_dir, exist_ok=True)
        
        # Decode Base64 and write to file
        credentials_data = base64.b64decode(credentials_base64)
        credentials_path = '/opt/app/google-ads-mcp/credentials.json'
        
        with open(credentials_path, 'wb') as f:
            f.write(credentials_data)
        
        # Set environment variable for Google client libraries
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        # Verify the JSON is valid
        with open(credentials_path, 'r') as f:
            json.load(f)  # This will raise exception if invalid JSON
        
        print("SUCCESS: Credentials file created and validated")
        return True, "Credentials successfully set up"
    except Exception as e:
        print(f"ERROR in setup_credentials: {str(e)}")
        return False, f"Error setting up credentials: {str(e)}"

# Setup credentials at startup
print("=== DEBUG: Calling setup_credentials ===")
CREDS_SUCCESS, CREDS_MESSAGE = setup_credentials()
print(f"=== DEBUG: setup_credentials result: {CREDS_SUCCESS}, {CREDS_MESSAGE} ===")

# Import Google Ads libraries
try:
    from google.ads.googleads.client import GoogleAdsClient
    from google.ads.googleads.v21.services.services.google_ads_service import GoogleAdsServiceClient
    import google.auth
    ADS_AVAILABLE = True
    
    # Initialize Google Ads client
    def _create_credentials():
        """Returns Application Default Credentials with read-only scope."""
        (credentials, _) = google.auth.default(scopes=["https://www.googleapis.com/auth/adwords"])
        return credentials
    
    def get_googleads_client():
        return GoogleAdsClient(
            credentials=_create_credentials(),
            developer_token=os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN"),
            login_customer_id=os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
        )
    
except ImportError as e:
    print(f"Import error: {e}")
    ADS_AVAILABLE = False

app = FastAPI(
    title="Google Ads Full API",
    description="Complete HTTP API for all Google Ads MCP tools",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    customer_id: str
    query: str

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Google Ads Full API",
        "version": "1.0.0",
        "status": "running",
        "ads_available": ADS_AVAILABLE,
        "credentials_set": CREDS_SUCCESS,
        "credentials_message": CREDS_MESSAGE,
        "mcp_tools": [
            "list_accessible_customers",
            "search"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "google-ads-full-api",
        "google_ads": ADS_AVAILABLE
    }

# ===== MCP TOOL 1: list_accessible_customers =====
@app.get("/customers")
def list_accessible_customers_endpoint():
    """HTTP endpoint for listing customers"""
    return list_accessible_customers_sync()

def list_accessible_customers_sync():
    """List accessible customers - MCP Tool: list_accessible_customers"""
    if not ADS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Google Ads libraries not available")
    
    try:
        client = get_googleads_client()
        customer_service = client.get_service("CustomerService")
        
        # Call the list_accessible_customers method
        accessible_customers = customer_service.list_accessible_customers()
        
        result = []
        for customer_resource_name in accessible_customers.resource_names:
            result.append({
                "resource_name": customer_resource_name,
                "customer_id": customer_resource_name.split('/')[-1]
            })
        
        return {
            "accessible_customers": result,
            "total_count": len(result)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching accessible customers: {str(e)}")

# ===== MCP TOOL 2: search =====
@app.post("/search")
def search_endpoint(search_request: SearchRequest):
    """HTTP endpoint for search"""
    return search_sync(search_request)

def search_sync(search_request: SearchRequest):
    """Search Google Ads data - MCP Tool: search"""
    if not ADS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Google Ads libraries not available")
    
    try:
        client = get_googleads_client()
        ga_service = client.get_service("GoogleAdsService")
        
        # Execute the search query
        search_request_obj = client.get_type("SearchGoogleAdsRequest")
        search_request_obj.customer_id = search_request.customer_id.replace('-', '')
        search_request_obj.query = search_request.query
        
        results = ga_service.search(request=search_request_obj)
        
        # Format results
        formatted_results = []
        for row in results:
            # Convert proto message to dict
            row_dict = {}
            for field in row._pb.DESCRIPTOR.fields:
                if hasattr(row, field.name):
                    value = getattr(row, field.name)
                    # Handle nested objects
                    if hasattr(value, '_pb'):
                        nested_dict = {}
                        for nested_field in value._pb.DESCRIPTOR.fields:
                            if hasattr(value, nested_field.name):
                                nested_dict[nested_field.name] = str(getattr(value, nested_field.name))
                        row_dict[field.name] = nested_dict
                    else:
                        row_dict[field.name] = str(value)
            
            formatted_results.append(row_dict)
        
        return {
            "customer_id": search_request.customer_id,
            "query": search_request.query,
            "results": formatted_results,
            "total_results": len(formatted_results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing search: {str(e)}")

# ===== HELPER ENDPOINTS =====
@app.get("/campaigns/{customer_id}")
def get_campaigns_endpoint(customer_id: str):
    """HTTP endpoint for campaigns"""
    return get_campaigns_sync(customer_id)

def get_campaigns_sync(customer_id: str):
    """Get campaigns for a customer - Helper endpoint"""
    search_request = SearchRequest(
        customer_id=customer_id,
        query="SELECT campaign.id, campaign.name, campaign.status FROM campaign"
    )
    return search_sync(search_request)

@app.get("/debug")
async def debug_endpoint():
    """Debug endpoint for credentials and status"""
    try:
        creds_path = '/opt/app/google-ads-mcp/credentials.json'
        file_exists = os.path.exists(creds_path)
        file_size = os.path.getsize(creds_path) if file_exists else 0
        
        return {
            "credentials_setup": {
                "success": CREDS_SUCCESS,
                "message": CREDS_MESSAGE
            },
            "file_status": {
                "exists": file_exists,
                "size": file_size
            },
            "environment": {
                "GOOGLE_APPLICATION_CREDENTIALS": os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
                "GOOGLE_CREDENTIALS_BASE64_LENGTH": len(os.environ.get("GOOGLE_CREDENTIALS_BASE64", "")),
                "GOOGLE_ADS_DEVELOPER_TOKEN": "***" if os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN") else "NOT_SET"
            },
            "ads_tools_status": {
                "ads_libraries_available": ADS_AVAILABLE,
                "credentials_configured": CREDS_SUCCESS,
                "all_tools_ready": ADS_AVAILABLE and CREDS_SUCCESS
            }
        }
    except Exception as e:
        return {"error": str(e)}

# ===== MCP PROTOCOL CLASSES =====
class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: str
    params: Optional[dict] = None

class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[dict] = None

# ===== MCP ENDPOINT WITH SSE =====
@app.post("/mcp")
@app.get("/mcp")
async def mcp_endpoint(request: Request):
    """MCP Protocol endpoint with Server-Sent Events support"""
    
    # Check Accept header for SSE
    accept = request.headers.get("accept", "")
    if "text/event-stream" not in accept:
        return {
            "jsonrpc": "2.0",
            "id": "server-error", 
            "error": {
                "code": -32600,
                "message": "Not Acceptable: Client must accept text/event-stream"
            }
        }
    
    # Check for session ID in query params or headers
    session_id = request.query_params.get("session_id") or request.headers.get("x-session-id")
    if not session_id:
        return {
            "jsonrpc": "2.0",
            "id": "server-error",
            "error": {
                "code": -32600,
                "message": "Bad Request: Missing session ID"
            }
        }
    
    async def event_stream() -> AsyncIterator[str]:
        """Generate MCP events"""
        try:
            # Send initial handshake
            yield json.dumps({
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            })
            
            # Send available tools
            tools = [
                {
                    "name": "list_accessible_customers",
                    "description": "List accessible Google Ads customers",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "search", 
                    "description": "Search Google Ads data using GAQL query",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "customer_id": {"type": "string", "description": "Customer ID (without dashes)"},
                            "query": {"type": "string", "description": "GAQL query string"}
                        },
                        "required": ["customer_id", "query"]
                    }
                },
                {
                    "name": "get_campaigns",
                    "description": "Get campaigns for a customer", 
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "customer_id": {"type": "string", "description": "Customer ID (without dashes)"}
                        },
                        "required": ["customer_id"]
                    }
                }
            ]
            
            yield json.dumps({
                "jsonrpc": "2.0",
                "method": "tools/list", 
                "params": {
                    "tools": tools
                }
            })
            
            # Keep connection alive
            while True:
                await asyncio.sleep(1)
                yield json.dumps({
                    "jsonrpc": "2.0",
                    "method": "notifications/ping",
                    "params": {"timestamp": int(asyncio.get_event_loop().time())}
                })
                
        except Exception as e:
            yield json.dumps({
                "jsonrpc": "2.0",
                "id": "server-error",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            })
    
    return EventSourceResponse(event_stream())

# ===== MCP TOOL EXECUTION =====
@app.post("/mcp/call/{tool_name}")
async def call_mcp_tool(tool_name: str, request: dict):
    """Execute MCP tool"""
    try:
        if tool_name == "list_accessible_customers":
            result = list_accessible_customers_sync()
        elif tool_name == "search":
            customer_id = request.get("customer_id")
            query = request.get("query")
            if not customer_id or not query:
                raise ValueError("Missing required parameters: customer_id, query")
            search_request = SearchRequest(customer_id=customer_id, query=query)
            result = search_sync(search_request)
        elif tool_name == "get_campaigns":
            customer_id = request.get("customer_id")
            if not customer_id:
                raise ValueError("Missing required parameter: customer_id")
            result = get_campaigns_sync(customer_id)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
            
        return {
            "jsonrpc": "2.0",
            "result": result
        }
        
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7777))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )
