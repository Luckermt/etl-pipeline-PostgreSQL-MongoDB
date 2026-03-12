# Ru
# Luckermt's система синхронизации данных PostgreSQL -> MongoDB

## Описание

Система для периодической синхронизации данных из PostgreSQL в MongoDB с поддержкой:

- Отслеживания созданий, обновлений и удалений

- Связи многие-ко-многим (orders ↔ products)

- Идемпотентности

- Денормализации данных в MongoDB

Синхронизация данных происходит каждые минуту по умолчанию, можно изменить в .env файле.

## Инструкция по запуску:

1. Запуск контейнеров.

docker-build up --build

2. Генерация данных.

docker-compose exec sync-script python /app/scripts/generate_data.py

3. Опционально, можно досрочно синхронизировать данные.

docker-compose exec sync-script python /app/scripts/sync.py

4. Опционально, можно проверить идемпотентность через готовый скрипт.

docker-compose exec sync-script python /app/scripts/test_idempotency.py

5. Опционально, вы можете настроить .env файл.

6. Интервал синхронизации можно настроить в cron/sync-cron, для этого нужно изменить 1 цифру на желаемое количество минут.


# En
# Luckermt's system of data synchronization PostgreSQL -> MongoDB

## Description

A system for periodic data synchronization from PostgreSQL to MongoDB with the support of:

- Tracking creations, updates, and deletions

- Many-to-many relationships (orders ↔ products)

- Idempotency

- Data denormalization in MongoDB

Synchronization happens every minute by default, can be changed in a .env file.

## Usage manual

1. Start the containers.

docker-build up --build

2. Generate test-data.

docker-compose exec sync-script python /app/scripts/generate_data.py

3. Optionally, you can synchronize data prematurely.

docker-compose exec sync-script python /app/scripts/sync.py

4. Optionally, you can test idempostency via a pre-made script.

docker-compose exec sync-script python /app/scripts/test_idempotency.py

5. Optionally, you can redact .env file.

6. Synchronization interval can be adjusted at cron/sync-cron, to do that,
you need to change the first number to the number of minutes you want.
