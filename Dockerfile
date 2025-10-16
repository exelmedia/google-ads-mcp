FROM python:3.11-slim

# Zainstaluj system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Zainstaluj pipx
RUN pip install pipx
RUN pipx ensurepath

# Dodaj pipx do PATH
ENV PATH="/root/.local/bin:$PATH"

# Ustaw working directory
WORKDIR /app

# Skopiuj kod źródłowy
COPY . .

# Zainstaluj pakiet
RUN pipx install .

# Expose port (domyślnie MCP używa stdio, ale dla celów serwera HTTP można dodać port)
EXPOSE 8000

# Uruchom serwer MCP
CMD ["google-ads-mcp"]