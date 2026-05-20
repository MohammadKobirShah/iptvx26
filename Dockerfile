# IPTV Restreaming System - Railway Deployment
# Ultra-low latency, no transcoding, copy mode only

FROM ubuntu:22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    xz-utils \
    python3 \
    python3-pip \
    nginx \
    supervisor \
    ca-certificates \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Install FFmpeg (static build for reliability)
RUN cd /tmp && \
    wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    tar xf ffmpeg-release-amd64-static.tar.xz && \
    cd ffmpeg-*-amd64-static && \
    cp ffmpeg ffprobe /usr/local/bin/ && \
    chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe && \
    cd / && rm -rf /tmp/*

# Install MediaMTX
RUN MEDIAMTX_VERSION=$(curl -s https://api.github.com/repos/bluenviron/mediamtx/releases/latest | grep -oP '"tag_name": "\K(.*)(?=")') && \
    wget https://github.com/bluenviron/mediamtx/releases/download/${MEDIAMTX_VERSION}/mediamtx_${MEDIAMTX_VERSION}_linux_amd64.tar.gz -O /tmp/mediamtx.tar.gz && \
    tar -xzf /tmp/mediamtx.tar.gz -C /usr/local/bin/ && \
    chmod +x /usr/local/bin/mediamtx && \
    rm /tmp/mediamtx.tar.gz

# Create app directory
WORKDIR /app

# Copy Python requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p /var/log/supervisor \
    /var/log/nginx \
    /var/log/mediamtx \
    /var/log/ffmpeg \
    /var/log/iptv \
    /run/nginx \
    /var/cache/nginx

# Copy configuration files
COPY configs/nginx.conf /etc/nginx/nginx.conf
COPY configs/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY configs/mediamtx.yml /etc/mediamtx.yml

# Make scripts executable
RUN chmod +x /app/scripts/*.sh

# Expose port (Railway will map this)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /app/scripts/healthcheck.sh || exit 1

# Start supervisor to manage all processes
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
