# Ru
# Luckermt's система синхронизации данных PostgreSQL -> MongoDB

## Описание

Система для периодической синхронизации данных из PostgreSQL в MongoDB с поддержкой:

- Отслеживания созданий, обновлений и удалений

- Связи многие-ко-многим (orders ↔ products)

- Идемпотентности

- Денормализации данных в MongoDB

Синхронизация данных происходит каждые 5 минут по умолчанию.

## Инструкция по запуску:
1. Создайте .env файл в корневой директории.
env
```
POSTGRES_USER=admin
POSTGRES_PASSWORD=secure_password_123
POSTGRES_DB=shop
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

MONGO_ROOT_USER=root
MONGO_ROOT_PASSWORD=secure_mongo_password_123
MONGO_DB=shop_replica
MONGO_HOST=mongodb
MONGO_PORT=27017

BATCH_SIZE=1000
SYNC_INTERVAL_MINUTES=5
```
2. Запуск контейнеров.

docker-build up --build

3. Генерация данных.

docker-compose exec sync-script python /app/scripts/generate_data.py

4. Опционально, можно досрочно синхронизировать данные.

docker-compose exec sync-script python /app/scripts/sync.py

5. Опционально, можно проверить идемпотентность через готовый скрипт.

docker-compose exec sync-script python /app/scripts/test_idempotency.py

6. Опционально, вы можете настроить .env файл.

7. Интервал синхронизации можно настроить в .env


# En
# Luckermt's system of data synchronization PostgreSQL -> MongoDB

## Description

A system for periodic data synchronization from PostgreSQL to MongoDB with the support of:

- Tracking creations, updates, and deletions

- Many-to-many relationships (orders ↔ products)

- Idempotency

- Data denormalization in MongoDB

Synchronization happens every 5 minutes by default.

## Usage manual

1. Create a .env file in the root directory.
env
```
POSTGRES_USER=admin
POSTGRES_PASSWORD=secure_password_123
POSTGRES_DB=shop
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

MONGO_ROOT_USER=root
MONGO_ROOT_PASSWORD=secure_mongo_password_123
MONGO_DB=shop_replica
MONGO_HOST=mongodb
MONGO_PORT=27017

BATCH_SIZE=1000
SYNC_INTERVAL_MINUTES=5
```
2. Start the containers.

docker-build up --build

3. Generate test-data.

docker-compose exec sync-script python /app/scripts/generate_data.py

4. Optionally, you can synchronize data prematurely.

docker-compose exec sync-script python /app/scripts/sync.py

5. Optionally, you can test idempostency via a pre-made script.

docker-compose exec sync-script python /app/scripts/test_idempotency.py

6. Optionally, you can redact .env file.

7. Synchronization interval can be adjusted in a .env file.
