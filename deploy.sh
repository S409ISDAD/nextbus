#!/bin/bash

set -e

echo "pulling code from repo..."
git pull

export COMMIT=$(git rev-parse --short HEAD)

echo "building version $COMMIT..."
docker compose -f docker-compose.prod.yml build

echo "starting..."
docker compose -f docker-compose.prod.yml up -d

echo "deployment complete."