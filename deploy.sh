#!/bin/bash

set -e

echo "pulling code from repo..."
git pull

echo "building..."
COMMIT=$(git rev-parse --short HEAD) docker-compose -f docker-compose.prod.yml build

echo "starting..."
docker compose -f docker-compose.prod.yml up -d

echo "deployment complete."