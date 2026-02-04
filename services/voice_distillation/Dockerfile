FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# System dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    ffmpeg \
    libsndfile1 \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Set python3.11 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Install pip for python3.11
RUN python -m ensurepip --upgrade && pip install --upgrade pip

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy pipeline code
COPY . /app
WORKDIR /app

# Pre-download Kokoro model and Spanish voices during build
RUN python -c "\
from kokoro import KPipeline; \
p = KPipeline(lang_code='e', model_id='hexgrad/Kokoro-82M'); \
print('Kokoro Spanish loaded successfully'); \
for v in ['ef_dora', 'em_alex', 'em_santa']: \
    try: \
        t = p.load_voice(v); \
        print(f'Voice {v}: shape={t.shape}'); \
    except: \
        print(f'Voice {v}: not available'); \
"

ENTRYPOINT ["python", "run_pipeline.py"]
