FROM python:3.11-slim

# Zainstaluj system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Zainstaluj dependencies bezpośrednio
RUN pip install google-ads mcp[cli] flask

# Ustaw working directory
WORKDIR /app

# Skopiuj kod źródłowy
COPY . .

# Create script to decode credentials from base64
RUN echo '#!/bin/bash' > /app/decode_credentials.sh && \
    echo 'if [ -n "$GOOGLE_CREDENTIALS_BASE64" ]; then' >> /app/decode_credentials.sh && \
    echo '  echo "$GOOGLE_CREDENTIALS_BASE64" | base64 -d > /app/credentials.json' >> /app/decode_credentials.sh && \
    echo 'fi' >> /app/decode_credentials.sh && \
    chmod +x /app/decode_credentials.sh

# Expose port for HTTP wrapper
EXPOSE 5001

# Default to HTTP wrapper for deployment
CMD ["sh", "-c", "/app/decode_credentials.sh && python http_wrapper.py"]
