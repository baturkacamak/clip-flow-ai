FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    imagemagick \
    git \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick policy for MoviePy if needed (allow read/write)
RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml

WORKDIR /app

# Install Python dependencies
# We use requirements.txt generated from poetry/pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create volumes for outputs and workspace
VOLUME /app/outputs
VOLUME /app/assets

# Entrypoint
ENTRYPOINT ["python", "cli.py"]
CMD ["--help"]
