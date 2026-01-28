FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libsndfile1 \
    ffmpeg \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for models and data
RUN mkdir -p /app/models /app/data/speakers /app/logs

# Copy application code
COPY . .

# Expose port
EXPOSE 8004

# Run the application
CMD ["uvicorn", "audio_server:app", "--host", "0.0.0.0", "--port", "8004"]
