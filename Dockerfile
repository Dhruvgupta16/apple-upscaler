# Apple Upscaler - Production Containerized Neural Remastering Environment
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies, FFmpeg, Vulkan drivers, and Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    ffmpeg \
    libvulkan1 \
    vulkan-tools \
    build-essential \
    cmake \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy source repository
COPY . .

# Build native C++ accelerator with CMake
RUN cmake -B build/native -S . && \
    cmake --build build/native --config Release

# Expose Webview / API port
EXPOSE 8080

# Default headless batch remaster worker command
CMD ["python3", "apple_upscaler.py", "--headless"]
