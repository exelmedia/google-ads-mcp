# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a Google Ads MCP (Model Context Protocol) Server that exposes Google Ads API functionality to LLMs through MCP tools. The server provides two main tools: `search` (for querying Google Ads data) and `list_accessible_customers` (for retrieving accessible customer accounts).

## Architecture

The codebase follows a modular structure:

- **`ads_mcp/coordinator.py`**: Contains the singleton FastMCP instance that coordinates tool registration
- **`ads_mcp/server.py`**: Entry point that imports tools and runs the MCP server
- **`ads_mcp/tools/`**: Tool implementations that register themselves with the coordinator using `@mcp.tool` decorators
  - `core.py`: Basic API methods (list_accessible_customers)
  - `search.py`: Complex search functionality with runtime-generated descriptions
- **`ads_mcp/utils.py`**: Google Ads API client setup and utility functions
- **`ads_mcp/mcp_header_interceptor.py`**: Custom interceptor for API request headers

Key architectural pattern: Tools self-register with the MCP coordinator using decorators, allowing modular addition of new functionality.

## Common Development Commands

### Testing
```bash
# Run all tests across Python versions
nox -s tests

# Run tests for specific Python version
nox -s tests-3.11

# Run single test file
python -m unittest tests.server_test -v
```

### Code Formatting & Linting
```bash
# Check formatting (fails if fixes needed)
nox -s lint

# Apply formatting fixes
nox -s format

# Manual black formatting
black -l 80 --exclude "/(v[0-9]+|\.eggs|\.git|_cache|\.nox|\.tox|\.venv|env|venv|\.svn|_build|buck-out|build|dist)/" .
```

### Running the Server
```bash
# Install and run via pipx
pipx install .
google-ads-mcp

# Run directly
python -m ads_mcp.server

# With environment variables
GOOGLE_ADS_DEVELOPER_TOKEN=your_token GOOGLE_PROJECT_ID=your_project python -m ads_mcp.server
```

### Docker Development
```bash
# Build image
docker-compose build

# Run with environment file
docker-compose up

# Run with inline environment variables
GOOGLE_PROJECT_ID=your_project GOOGLE_ADS_DEVELOPER_TOKEN=your_token docker-compose up
```

## Environment Configuration

Required environment variables:
- `GOOGLE_ADS_DEVELOPER_TOKEN`: Google Ads API developer token
- `GOOGLE_PROJECT_ID`: Google Cloud project ID

Optional:
- `GOOGLE_ADS_LOGIN_CUSTOMER_ID`: Manager account customer ID
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account JSON

Authentication methods:
1. Application Default Credentials (recommended for development)
2. Service account JSON file
3. Google Ads API client library configuration (google-ads.yaml)

## Tool Development

When adding new tools:

1. Create tool function in appropriate module under `ads_mcp/tools/`
2. Import `from ads_mcp.coordinator import mcp`
3. Register tool using `@mcp.tool()` decorator or `mcp.add_tool()` for complex descriptions
4. Import the module in `ads_mcp/server.py` to ensure registration
5. Use `ads_mcp.utils.get_googleads_service()` for API access

Example tool structure:
```python
from ads_mcp.coordinator import mcp
import ads_mcp.utils as utils

@mcp.tool()
def my_new_tool(customer_id: str) -> dict:
    """Tool description for LLM."""
    service = utils.get_googleads_service("SomeService")
    # Implementation
    return result
```

## Security Considerations

- Never commit actual credentials to the repository
- Use environment variables for sensitive configuration
- The server adds usage tracking headers to API requests via `MCPHeaderInterceptor`
- Credentials should use minimal required scopes (`https://www.googleapis.com/auth/adwords`)

## Deployment

The project includes elast.io deployment configuration in `DEPLOYMENT_ELAST.md` with:
- Build command: `docker-compose build`
- Run command: `docker-compose up`  
- Target: `172.17.0.1:8000`
- Required environment variables as listed above

## Dependencies

- Python 3.10+
- `google-ads>=28.0.0`: Google Ads API client
- `mcp[cli]>=1.2.0`: Model Context Protocol framework
- Development: `black` formatter, `nox` for testing