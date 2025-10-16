FROM python:3.11-slim

# Zainstaluj system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
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

# Expose port for HTTP wrapper
EXPOSE 5001

# Default to HTTP wrapper for deployment
CMD ["python", "http_wrapper.py"]
