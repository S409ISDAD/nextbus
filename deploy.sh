#!/bin/bash

set -e

echo "pulling code from repo..."
git pull origin main

echo "stopping containers..."
docker compose stop

echo "rebuilding and starting containers..."
docker compose up --build -d

echo "deployment complete."