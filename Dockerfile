# Stage 1: Build frontend
FROM node:18-alpine as frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

COPY frontend/ .
RUN npm run build

# Stage 2: Build backend
FROM python:3.11-slim as backend-builder

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Stage 3: Final image with nginx
FROM python:3.11-slim

WORKDIR /app

# Install nginx
RUN apt-get update && apt-get install -y nginx curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy entire app directory from backend builder (includes dependencies)
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin
COPY --from=backend-builder /app /app

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist /var/www/html

# Create startup script with proper newlines
RUN printf '#!/bin/bash\nnginx -g "daemon off;" &\ncd /app && python -m uvicorn main:app --host 0.0.0.0 --port 8000\n' > /start.sh && chmod +x /start.sh

# Configure nginx with longer timeouts for LLM calls
RUN printf 'server {\n    listen 80;\n    server_name _;\n    root /var/www/html;\n    index index.html;\n\n    location / {\n        try_files $uri $uri/ /index.html;\n    }\n\n    location /api {\n        proxy_pass http://127.0.0.1:8000;\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;\n        proxy_connect_timeout 300s;\n        proxy_send_timeout 300s;\n        proxy_read_timeout 300s;\n    }\n\n    location /health {\n        proxy_pass http://127.0.0.1:8000;\n    }\n}\n' > /etc/nginx/sites-available/default

# Create data directories
RUN mkdir -p /data/{config,runs,reports}

EXPOSE 80

CMD ["/start.sh"]
