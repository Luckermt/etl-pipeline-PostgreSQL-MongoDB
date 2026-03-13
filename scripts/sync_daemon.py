import os
import time
import signal
import sys
from loguru import logger
from sync import main as sync_main

logger.remove()
logger.add(sys.stderr, format="{time} {level} {message}", level="INFO")

running = True

def signal_handler(signum, frame):
    logger.info(f"Получен сигнал {signum}, завершаем работу...")
    global running
    running = False

def job():
    logger.info("Запуск плановой синхронизации...")
    try:
        sync_main()
    except Exception as e:
        logger.error(f"Ошибка при выполнении синхронизации: {e}")

def main():
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    interval_minutes = int(os.getenv("SYNC_INTERVAL_MINUTES", "1"))
    logger.info(f"Демон синхронизации запущен. Интервал: {interval_minutes} мин.")

    import schedule
    schedule.every(interval_minutes).minutes.do(job)

    job()

    while running:
        schedule.run_pending()
        time.sleep(1)

    logger.info("Демон остановлен.")

if __name__ == "__main__":
    main()