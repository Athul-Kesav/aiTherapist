FROM python:3.11

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y git curl && \
    rm -rf /var/lib/apt/lists/*

# Install git-lfs (optional, only if needed for your repo)
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && \
    apt-get install -y git-lfs && \
    git lfs install

# Copy Python dependencies and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code and models
COPY . .

EXPOSE 5173

CMD ["python", "main_api.py"]
