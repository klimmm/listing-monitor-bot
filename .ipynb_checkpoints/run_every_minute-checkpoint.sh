#!/bin/bash
# Script to run CIAN parser every minute

cd "$(dirname "$0")"

while true; do
    echo "$(date): Running CIAN parser..."
    python parse_cian.py
    echo "$(date): Completed. Waiting 60 seconds..."
    sleep 60
done