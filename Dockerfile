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

# Expose port for HTTP wrapper
EXPOSE 5001

# Default to HTTP wrapper for deployment
CMD ["python", "http_wrapper.py"]
