FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

WORKDIR /app

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-venv \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks
RUN ln -sf /usr/bin/python3.11 /usr/bin/python

# Upgrade pip
RUN python -m pip install --upgrade pip

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install F5-TTS Spanish
RUN pip install --no-cache-dir git+https://github.com/jpgallegoar/Spanish-F5

# Copy application
COPY . .

# Create models directory
RUN mkdir -p /app/models

EXPOSE 8001

CMD ["uvicorn", "tts_server:app", "--host", "0.0.0.0", "--port", "8001"]
