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
COPY init_data.sh ./
COPY alembic.ini ./

ARG COMMIT=dev
RUN echo "$COMMIT" > /app/version.txt

EXPOSE 8000

CMD ["gunicorn", "backend.main:app", \
    # "-w", "5", \
    "-w", "1", \
    "-k", "uvicorn.workers.UvicornWorker", \
    "--bind", "0.0.0.0:8000", \
    "--access-logfile", "-"]