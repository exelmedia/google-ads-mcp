FROM python:3.11-slim

# Zainstaluj system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Zainstaluj dependencies bezpośrednio
RUN pip install google-ads mcp[cli] fastapi uvicorn python-dotenv

# Ustaw working directory
WORKDIR /app

# Skopiuj kod źródłowy
COPY . .

# Create entrypoint script
RUN echo '#!/bin/bash' > /entrypoint.sh && \
    echo 'if [ -n "$GOOGLE_CREDENTIALS_BASE64" ]; then' >> /entrypoint.sh && \
    echo '  echo "$GOOGLE_CREDENTIALS_BASE64" | base64 -d > /app/credentials.json' >> /entrypoint.sh && \
    echo '  export GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json' >> /entrypoint.sh && \
    echo 'fi' >> /entrypoint.sh && \
    echo 'exec uvicorn full_ads_api:app --host 0.0.0.0 --port 7777' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Expose port for HTTP wrapper
EXPOSE 7777

# Use entrypoint
ENTRYPOINT ["/entrypoint.sh"]
