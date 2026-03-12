import asyncio
from sync import DataSync
from loguru import logger

def test_idempotency():
    """Тест идемпотентности - повторный запуск не должен создавать дубликаты"""
    syncer = DataSync()
    
    try:
        logger.info("First sync run...")
        syncer.sync()
        
        mongo_count_before = syncer.mongo_db.customers.count_documents({})
        
        logger.info("Second sync run...")
        syncer.sync()
        
        mongo_count_after = syncer.mongo_db.customers.count_documents({})
        
        if mongo_count_before == mongo_count_after:
            logger.success("Idempotency test passed! No duplicates created.")
        else:
            logger.error(f"Idempotency test failed! Count changed: {mongo_count_before} -> {mongo_count_after}")
            
    finally:
        syncer.close()

if __name__ == "__main__":
    test_idempotency()