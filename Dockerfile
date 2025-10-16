FROM python:3.10

WORKDIR /app

# Copy requirements and install dependencies
COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Install the package in editable mode for MCP server
RUN pip install -e .

# Expose port 7777
EXPOSE 7777

# Run the MCP server with credentials setup
CMD ["python3", "start_mcp.py"]
