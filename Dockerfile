FROM python:3.12-slim

# Set working directory & environment variables
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY requirements.txt pyproject.toml ./

# Install python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy source code and configurations
COPY config/ ./config/
COPY src/ ./src/
COPY README.md ./

# Create output directory
RUN mkdir -p /app/outputs

# Expose FastAPI port
EXPOSE 8000

# Default entrypoint starts the API server
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
