FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=7860 \
    HOST=0.0.0.0

WORKDIR /app

# Install system dependencies required by OpenCV and PyTorch
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    git \
    git-lfs \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create runtime directories
RUN mkdir -p uploads outputs Models

# Copy application files
COPY backend/ ./backend/
COPY static/ ./static/
COPY run.py .
COPY .env.example .env

# Copy Models folder if present locally
COPY Models/ ./Models/

# Create Hugging Face Spaces non-root user (UID 1000)
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 777 /app/uploads /app/outputs

USER appuser

EXPOSE 7860

CMD ["python", "run.py"]
