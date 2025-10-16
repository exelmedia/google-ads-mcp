#!/usr/bin/env python3
"""
Google Ads MCP Server using fastmcp
Based on the working GA MCP API pattern
"""

import os
import base64
import json
from typing import Any
from fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup credentials from Base64 if available
def setup_credentials():
    """Setup Google credentials from Base64 environment variable"""
    credentials_base64 = os.environ.get('GOOGLE_CREDENTIALS_BASE64')
    if credentials_base64:
        try:
            # Use tmp directory which should be writable
            os.makedirs('/tmp', exist_ok=True)
            
            # Decode Base64 and write to file
            credentials_data = base64.b64decode(credentials_base64)
            credentials_path = '/tmp/credentials.json'
            
            with open(credentials_path, 'wb') as f:
                f.write(credentials_data)
            
            # Set environment variable for Google client libraries
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            
            return True
        except Exception as e:
            print(f"Error setting up credentials: {e}")
            return False
    return True

# Setup credentials at startup
setup_credentials()

# Initialize FastMCP
mcp = FastMCP("Google Ads MCP")

try:
    from google.ads.googleads.client import GoogleAdsClient
    import google.auth
    
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
    
    ADS_AVAILABLE = True
except ImportError as e:
    print(f"Google Ads import error: {e}")
    ADS_AVAILABLE = False

@mcp.tool()
def list_accessible_customers() -> dict[str, Any]:
    """List accessible Google Ads customers"""
    if not ADS_AVAILABLE:
        return {"error": "Google Ads libraries not available"}
    
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
        return {"error": f"Error fetching accessible customers: {str(e)}"}

@mcp.tool()
def search(customer_id: str, query: str) -> dict[str, Any]:
    """Search Google Ads data using GAQL query
    
    Args:
        customer_id: The customer ID (without dashes)
        query: GAQL query string
    """
    if not ADS_AVAILABLE:
        return {"error": "Google Ads libraries not available"}
    
    try:
        client = get_googleads_client()
        ga_service = client.get_service("GoogleAdsService")
        
        # Execute the search query
        search_request_obj = client.get_type("SearchGoogleAdsRequest")
        search_request_obj.customer_id = customer_id.replace('-', '')
        search_request_obj.query = query
        
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
            "customer_id": customer_id,
            "query": query,
            "results": formatted_results,
            "total_results": len(formatted_results)
        }
        
    except Exception as e:
        return {"error": f"Error executing search: {str(e)}"}

@mcp.tool()
def get_campaigns(customer_id: str) -> dict[str, Any]:
    """Get campaigns for a customer
    
    Args:
        customer_id: The customer ID (without dashes)
    """
    query = "SELECT campaign.id, campaign.name, campaign.status FROM campaign"
    return search(customer_id, query)

def main():
    """Main entry point for the server"""
    mcp.run()

if __name__ == "__main__":
    main()
