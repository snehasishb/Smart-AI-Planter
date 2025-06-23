#!/bin/bash

# Wait until Wi-Fi has an IP address
echo "Waiting for Wi-Fi connection..."
while ! hostname -I | grep -qE '\b192\.168\.|10\.|172\.'; do
    sleep 1
done

echo "Wi-Fi connected, starting flashbrowser.py..."
python3 /home/pi/flashbrowser.py >> /home/pi/flashbrowser.log 2>&1
