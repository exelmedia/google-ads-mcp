#!/usr/bin/env python

# Copyright 2025 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Common utilities used by the MCP server."""

from typing import Any
import proto
import logging
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.v21.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)

from google.ads.googleads.util import get_nested_attr
import google.auth
from ads_mcp.mcp_header_interceptor import MCPHeaderInterceptor
import os

GAQL_FILEPATH = "ads_mcp/gaql_resources.txt"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Read-only scope for Analytics Admin API and Analytics Data API.
_READ_ONLY_ADS_SCOPE = "https://www.googleapis.com/auth/adwords"


def _create_credentials() -> google.auth.credentials.Credentials:
    """Returns Application Default Credentials with read-only scope."""
    (credentials, _) = google.auth.default(scopes=[_READ_ONLY_ADS_SCOPE])
    return credentials


def _get_developer_token() -> str:
    """Returns the developer token from the environment variable GOOGLE_ADS_DEVELOPER_TOKEN."""
    dev_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")
    if dev_token is None:
        raise ValueError(
            "GOOGLE_ADS_DEVELOPER_TOKEN environment variable not set."
        )
    return dev_token


def _get_login_customer_id() -> str:
    """Returns login customer id, if set, from the environment variable GOOGLE_ADS_LOGIN_CUSTOMER_ID."""
    return os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")


def _get_googleads_client() -> GoogleAdsClient:
    # Use this line if you have a google-ads.yaml file
    # client = GoogleAdsClient.load_from_storage()
    client = GoogleAdsClient(
        credentials=_create_credentials(),
        developer_token=_get_developer_token(),
        login_customer_id=_get_login_customer_id()
    )

    return client


_googleads_client = _get_googleads_client()


def get_googleads_service(serviceName: str) -> GoogleAdsServiceClient:
    return _googleads_client.get_service(
        serviceName, interceptors=[MCPHeaderInterceptor()]
    )


def get_googleads_type(typeName: str):
    return _googleads_client.get_type(typeName)


def _ensure_serializable(obj: Any) -> Any:
    """Recursively convert objects to JSON-serializable types."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, proto.Enum):
        return obj.name
    elif hasattr(obj, '_pb'):  # Protocol Buffer objects
        return str(obj)
    elif isinstance(obj, dict):
        return {key: _ensure_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_ensure_serializable(item) for item in obj]
    else:
        # Fallback to string conversion for any other type
        return str(obj)


def format_output_value(value: Any) -> Any:
    """Format a single value for safe JSON serialization."""
    try:
        return _ensure_serializable(value)
    except Exception as e:
        logger.warning(f"Error formatting value {type(value)}: {e}")
        return str(value)


def format_output_row(row: proto.Message, attributes):
    """Format a row for safe JSON serialization, avoiding protobuf errors."""
    result = {}
    for attr in attributes:
        try:
            value = get_nested_attr(row, attr)
            result[attr] = format_output_value(value)
        except Exception as e:
            logger.warning(f"Error getting attribute {attr}: {e}")
            result[attr] = f"Error: {str(e)}"
    
    # Final safety check - ensure entire result is serializable
    try:
        import json
        json.dumps(result)  # Test serialization
        return result
    except Exception as e:
        logger.error(f"Row serialization failed: {e}")
        # Return a safe fallback
        return {attr: str(getattr(row, attr.split('.')[0], 'N/A')) for attr in attributes}
