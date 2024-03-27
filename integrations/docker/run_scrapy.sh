#!/bin/bash
set -e
# Run example test from inside Docker image
echo "Running example SeleniumBase test from Docker with headless Chrome..."
cd /SeleniumBase/examples/scrapy && pytest index.py
exec "$@"
