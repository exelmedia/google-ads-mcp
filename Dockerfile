FROM python:3.11-slim

# Zainstaluj system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Ustaw working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
COPY pyproject.toml .

# Skopiuj kod źródłowy
COPY . .

# Install dependencies from requirements.txt and then install package
RUN pip install --no-cache-dir -r requirements.txt && pip install -e .

# Create entrypoint script
RUN echo '#!/bin/bash' > /entrypoint.sh && \
    echo 'if [ -n "$GOOGLE_CREDENTIALS_BASE64" ]; then' >> /entrypoint.sh && \
    echo '  echo "$GOOGLE_CREDENTIALS_BASE64" | base64 -d > /app/credentials.json' >> /entrypoint.sh && \
    echo '  export GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json' >> /entrypoint.sh && \
    echo 'fi' >> /entrypoint.sh && \
    echo 'exec fastmcp run google_ads_mcp_server.py --transport http --host 0.0.0.0 --port 7777' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Expose port for HTTP wrapper
EXPOSE 7777

# Use entrypoint
ENTRYPOINT ["/entrypoint.sh"]
