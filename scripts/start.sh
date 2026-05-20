#!/bin/bash

echo "Starting IPTV Restreaming System..."

# Wait for network
sleep 5

# Start supervisor (which starts all services)
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
