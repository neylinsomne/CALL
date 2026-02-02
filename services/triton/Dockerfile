FROM nvcr.io/nvidia/tritonserver:24.01-py3

# Install faster-whisper and dependencies for the Python backend
RUN pip install --no-cache-dir \
    faster-whisper==1.0.1 \
    numpy==1.26.3

# Create directory for cached models
RUN mkdir -p /models/whisper

# Model repository is mounted via docker volume
# CMD uses custom ports to avoid conflicts with other services
CMD ["tritonserver", \
     "--model-repository=/model_repository", \
     "--http-port=8010", \
     "--grpc-port=8011", \
     "--metrics-port=8012", \
     "--log-verbose=1"]
