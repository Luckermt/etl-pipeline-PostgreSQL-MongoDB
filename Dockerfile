FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY scripts/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ /app/scripts/

RUN apt-get update && apt-get install -y cron
COPY cron/sync-cron /etc/cron.d/sync-cron
RUN chmod 0644 /etc/cron.d/sync-cron

RUN mkdir -p /var/log/sync && chmod 777 /var/log/sync
CMD ["cron", "-f"]