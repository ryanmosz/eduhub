#!/bin/bash
# Quick script to run frontend in Docker for development

echo "🚀 Starting EduHub Frontend in Docker..."

# Build the image
docker build -t eduhub-frontend:dev .

# Run with volume mounts for hot reload
docker run -it --rm \
  -p 5173:5173 \
  -v $(pwd)/src:/app/src \
  -v $(pwd)/public:/app/public \
  -v $(pwd)/index.html:/app/index.html \
  --name eduhub-frontend \
  eduhub-frontend:dev