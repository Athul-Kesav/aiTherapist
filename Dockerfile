FROM python:3.11

# ---------------- System deps ----------------
RUN apt-get update && \
    apt-get install -y git curl libgl1 libglib2.0-0 ffmpeg supervisor && \
    rm -rf /var/lib/apt/lists/*

# Git LFS
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && \
    apt-get install -y git-lfs && \
    git lfs install

# Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# ---------------- App code ----------------
WORKDIR /app

# Python backend
COPY ourModels/VideoAndAudioAnalysis/requirements.txt ./ourModels/VideoAndAudioAnalysis/
RUN pip install --no-cache-dir -r ourModels/VideoAndAudioAnalysis/requirements.txt

COPY ourModels/TTS/test_bark.py ./ourModels/TTS

# Next.js frontend
WORKDIR /app/my-app
COPY my-app/package*.json ./
RUN npm install
COPY my-app ./
RUN npm run build

# Copy Python backend + supervisord config + entrypoint
WORKDIR /app
COPY ourModels ./ourModels
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose ports
EXPOSE 3000 5173

# Start everything
CMD ["/app/entrypoint.sh"]
