FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY README.md .
COPY src/ ./src/

# Install the full package with all extensions
RUN uv pip install --system ".[full]"

# Set path and expose ports
ENV PYTHONPATH=/app/src
EXPOSE 8000 8501

# Command is provided by docker-compose
CMD ["uvicorn", "systemictau.platform.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
