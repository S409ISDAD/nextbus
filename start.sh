#!/bin/sh
python -m fastapi run backend/main.py --proxy-headers --port 8000 --host 0.0.0.0 &

nginx -g 'daemon off;'