FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including pytest
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Run RQ worker
CMD ["python", "worker.py"]

