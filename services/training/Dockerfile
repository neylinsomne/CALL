FROM nvidia/cuda:12.1-runtime-ubuntu22.04

WORKDIR /app

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-venv \
    git \
    ffmpeg \
    sox \
    libsox-fmt-all \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3.11 /usr/bin/python

RUN python -m pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install F5-TTS for training
RUN pip install --no-cache-dir git+https://github.com/jpgallegoar/Spanish-F5

COPY . .

RUN mkdir -p /app/data /app/checkpoints /app/output

# Default command shows help
CMD ["python", "finetune.py", "--help"]
