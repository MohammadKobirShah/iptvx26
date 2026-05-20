#!/bin/bash

# Check if nginx is responding
if ! curl -sf http://localhost:8080/health > /dev/null; then
    echo "Nginx not responding"
    exit 1
fi

# Check if API is responding
if ! curl -sf http://localhost:5000/health > /dev/null; then
    echo "API not responding"
    exit 1
fi

# Check if MediaMTX is running
if ! pgrep -x mediamtx > /dev/null; then
    echo "MediaMTX not running"
    exit 1
fi

echo "Health check passed"
exit 0
