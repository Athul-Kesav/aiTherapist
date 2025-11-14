FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# Install Python + dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# Fix pip default
RUN ln -s /usr/bin/python3 /usr/bin/python

# Install PyTorch (CUDA 11.8 build)
RUN pip install --upgrade pip
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install Bark + SciPy
RUN pip install git+https://github.com/suno-ai/bark.git
RUN pip install scipy soundfile

# Copy source
WORKDIR /app
COPY test_bark.py .

CMD ["python", "test_bark.py"]
