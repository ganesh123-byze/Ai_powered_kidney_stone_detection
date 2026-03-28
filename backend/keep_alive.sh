#!/bin/bash
# ============================================================================
# Keep-Alive Service - Prevents Render Free Tier Hibernation
# ============================================================================
# This script is meant to be run periodically (every 14 minutes) via:
# - GitHub Actions (free)
# - EasyCron (free)
# - Other free cron services
# 
# Purpose: Ping the backend API to keep it warm and prevent hibernation
# on Render's free tier (which sleeps after 15 minutes of inactivity)

set -e

BACKEND_URL="${BACKEND_URL:-https://kidney-detection-backend.onrender.com}"
HEALTH_ENDPOINT="$BACKEND_URL/health"
LOG_FILE="keep_alive.log"

# Timestamp
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Append to log
echo "[$TIMESTAMP] Pinging: $HEALTH_ENDPOINT" >> "$LOG_FILE"

# Ping the backend health endpoint
if curl -f -s "$HEALTH_ENDPOINT" > /dev/null 2>&1; then
    echo "[$TIMESTAMP] ✅ Backend is warm!" >> "$LOG_FILE"
    exit 0
else
    echo "[$TIMESTAMP] ⚠️  Backend might be sleeping (this is normal if first request)" >> "$LOG_FILE"
    exit 0
fi
