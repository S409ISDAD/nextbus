# === Stage 1: Build frontend ===
FROM node:24-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install
COPY frontend ./frontend
RUN cd frontend && npm run build

# === Stage 2: Final container with backend + frontend ===
FROM python:3.13

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends bash gdal-bin && \
    rm -rf /var/lib/apt/lists/* /var/lib/apt /var/lib/dpkg/info/*
WORKDIR /app

# Copy backend code and install Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY static_data ./static_data

COPY --from=frontend-builder /app/frontend/dist ./frontend_dist

EXPOSE 8000
CMD ["fastapi", "run", "backend/main.py", "--proxy-headers", "--port", "8000", "--host", "0.0.0.0"]