FROM python:3.11-slim
# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
  && rm -rf /var/lib/apt/lists/*
# Allow build-time UID/GID injection
ARG HOST_UID
ARG HOST_GID
# Create a non-root user matching your host UID/GID
RUN groupadd -g ${HOST_GID} obsidian && \
    useradd -m -u ${HOST_UID} -g obsidian obsidian
# Prepare work dir
WORKDIR /app
# Copy requirements first for better layer caching
COPY requirements.txt .
# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt
# Copy application code
COPY . .
# Make sure your input/output/logs dirs exist
RUN mkdir -p /app/input /app/output /app/processed /app/logs
# Chown everything to your non-root user
RUN chown -R obsidian:obsidian /app
# Switch to the non-root user
USER obsidian
# Default command
CMD ["python", "meeting_processor.py"]