import json
import hashlib
import os
from datetime import datetime
from typing import Dict, List, Optional
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from loguru import logger
import sys

load_dotenv()
logger.remove()
logger.add(sys.stderr, format="{time} {level} {message}", level="INFO")
class DataSync:
    def __init__(self):
        self.pg_conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            database=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            cursor_factory=RealDictCursor
        )
        
        mongo_client = MongoClient(
            host=os.getenv('MONGO_HOST'),
            port=int(os.getenv('MONGO_PORT')),
            username=os.getenv('MONGO_ROOT_USER'),
            password=os.getenv('MONGO_ROOT_PASSWORD')
        )
        self.mongo_db = mongo_client[os.getenv('MONGO_DB')]
        
        self.state_file = '/tmp/sync_state.json'
        self.batch_size = int(os.getenv('BATCH_SIZE', 1000))
        
        self._ensure_indexes()
        
        self._init_state_file()
    
    def _init_state_file(self):
        try:
            if not os.path.exists(self.state_file):
                initial_state = {
                    'last_sync': datetime.now().replace(
                        hour=0, minute=0, second=0, microsecond=0
                    ).isoformat()
                }
                with open(self.state_file, 'w') as f:
                    json.dump(initial_state, f)
                logger.info(f"Created new state file: {self.state_file}")
        except Exception as e:
            logger.warning(f"Could not initialize state file: {e}")
    
    def _ensure_indexes(self):
        try:
            customers = self.mongo_db.customers
            customers.create_index('email', unique=True)
            customers.create_index('synced_at')
            customers.create_index('deleted_at')
            customers.create_index('_hash')
            logger.info("MongoDB indexes created/verified")
        except Exception as e:
            logger.warning(f"Could not create MongoDB indexes: {e}")
    
    def _get_last_sync_time(self) -> datetime:
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                return datetime.fromisoformat(state['last_sync'])
        except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as e:
            logger.warning(f"Could not read state file: {e}, using default")
            return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    def _save_sync_time(self, sync_time: datetime):
        try:
            temp_file = f"{self.state_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump({'last_sync': sync_time.isoformat()}, f)
            os.replace(temp_file, self.state_file)
            logger.debug(f"Saved sync time: {sync_time}")
        except Exception as e:
            logger.error(f"Failed to save sync time: {e}")
    
    def _calculate_hash(self, data: Dict) -> str:
        hash_string = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def _format_datetime(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, str):
            return value
        return str(value)
    
    def _get_changed_customers(self, last_sync: datetime) -> List[Dict]:
        with self.pg_conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.*,
                    COALESCE(
                        json_agg(
                            json_build_object(
                                'order_id', o.id,
                                'status', o.status,
                                'created_at', o.created_at,
                                'updated_at', o.updated_at,
                                'deleted_at', o.deleted_at,
                                'products', (
                                    SELECT json_agg(
                                        json_build_object(
                                            'product_id', p.id,
                                            'name', p.name,
                                            'price', p.price,
                                            'quantity', op.quantity,
                                            'price_at_time', op.price_at_time
                                        )
                                    )
                                    FROM order_products op
                                    JOIN products p ON p.id = op.product_id
                                    WHERE op.order_id = o.id
                                )
                            )
                        ) FILTER (WHERE o.id IS NOT NULL),
                        '[]'::json
                    ) as orders
                FROM customers c
                LEFT JOIN orders o ON o.customer_id = c.id 
                    AND (o.updated_at > %s OR o.deleted_at > %s OR o.deleted_at IS NOT NULL)
                WHERE 
                    c.updated_at > %s 
                    OR c.created_at > %s 
                    OR c.deleted_at > %s 
                    OR c.deleted_at IS NOT NULL
                GROUP BY c.id
            """, (last_sync, last_sync, last_sync, last_sync, last_sync))
            
            return cursor.fetchall()
    
    def _get_changed_orders_without_customer(self, last_sync: datetime) -> List[Dict]:
        with self.pg_conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    o.*,
                    COALESCE(
                        json_agg(
                            json_build_object(
                                'product_id', p.id,
                                'name', p.name,
                                'price', p.price,
                                'quantity', op.quantity,
                                'price_at_time', op.price_at_time
                            )
                        ) FILTER (WHERE p.id IS NOT NULL),
                        '[]'::json
                    ) as products
                FROM orders o
                LEFT JOIN order_products op ON op.order_id = o.id
                LEFT JOIN products p ON p.id = op.product_id
                WHERE 
                    (o.updated_at > %s OR o.deleted_at > %s)
                    AND NOT EXISTS (
                        SELECT 1 FROM customers c 
                        WHERE c.id = o.customer_id 
                        AND (c.updated_at > %s OR c.deleted_at > %s)
                    )
                GROUP BY o.id
            """, (last_sync, last_sync, last_sync, last_sync))
            
            return cursor.fetchall()
    
    def _get_deleted_records(self, last_sync: datetime) -> Dict:
        with self.pg_conn.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM customers 
                WHERE deleted_at > %s
            """, (last_sync,))
            deleted_customers = [row['id'] for row in cursor.fetchall()]
            
            cursor.execute("""
                SELECT id, customer_id FROM orders 
                WHERE deleted_at > %s
            """, (last_sync,))
            deleted_orders = cursor.fetchall()
            
            return {
                'customers': deleted_customers,
                'orders': deleted_orders
            }
    
    def _sync_to_mongodb(self, customers_data: List[Dict], deleted_records: Dict):
        customers_collection = self.mongo_db.customers
        
        bulk_operations = []
        
        for customer in customers_data:
            customer_dict = dict(customer)
            
            for field in ['created_at', 'updated_at', 'deleted_at']:
                if field in customer_dict:
                    customer_dict[field] = self._format_datetime(customer_dict[field])
            
            data_hash = self._calculate_hash(customer_dict)
            customer_dict['_hash'] = data_hash
            customer_dict['synced_at'] = datetime.now().isoformat()
            
            orders = customer_dict.pop('orders', [])
            processed_orders = []
            
            for order in orders:
                if order and isinstance(order, dict):
                    for field in ['created_at', 'updated_at', 'deleted_at', 'placed_at']:
                        if field in order:
                            order[field] = self._format_datetime(order[field])
                    
                    if 'products' in order and order['products']:
                        products = order['products']
                        if isinstance(products, list):
                            for product in products:
                                if product and isinstance(product, dict):
                                    for field in ['created_at', 'updated_at']:
                                        if field in product:
                                            product[field] = self._format_datetime(product[field])
                    
                    processed_orders.append(order)
            
            customer_dict['orders'] = processed_orders
            
            bulk_operations.append(
                UpdateOne(
                    {'_id': customer_dict['id']},
                    {'$set': customer_dict},
                    upsert=True
                )
            )
        
        for customer_id in deleted_records['customers']:
            bulk_operations.append(
                UpdateOne(
                    {'_id': customer_id},
                    {'$set': {'deleted_at': datetime.now().isoformat()}}
                )
            )
        
        for order in deleted_records['orders']:
            bulk_operations.append(
                UpdateOne(
                    {'_id': order['customer_id']},
                    {'$pull': {'orders': {'order_id': order['id']}}}
                )
            )
        
        if bulk_operations:
            try:
                result = customers_collection.bulk_write(bulk_operations, ordered=False)
                logger.info(f"MongoDB sync completed: "
                           f"Matched: {result.matched_count}, "
                           f"Modified: {result.modified_count}, "
                           f"Upserted: {result.upserted_count}")
            except BulkWriteError as bwe:
                logger.error(f"Bulk write error: {bwe.details}")
    
    def sync(self):
        try:
            last_sync = self._get_last_sync_time()
            current_sync = datetime.now()
            
            logger.info(f"Starting sync from {last_sync} to {current_sync}")
            
            changed_customers = self._get_changed_customers(last_sync)
            changed_orders = self._get_changed_orders_without_customer(last_sync)
            deleted_records = self._get_deleted_records(last_sync)
            
            logger.info(f"Found {len(changed_customers)} changed customers, "
                       f"{len(changed_orders)} orders without customer changes, "
                       f"{len(deleted_records['customers'])} deleted customers, "
                       f"{len(deleted_records['orders'])} deleted orders")
            
            customers_dict = {c['id']: c for c in changed_customers}
            
            for order in changed_orders:
                customer_id = order['customer_id']
                if customer_id in customers_dict:
                    if 'orders' not in customers_dict[customer_id]:
                        customers_dict[customer_id]['orders'] = []
                    customers_dict[customer_id]['orders'].append(order)
                else:
                    with self.pg_conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT * FROM customers WHERE id = %s
                        """, (customer_id,))
                        customer = cursor.fetchone()
                        if customer:
                            customer_dict = dict(customer)
                            customer_dict['orders'] = [order]
                            customers_dict[customer_id] = customer_dict
            
            if customers_dict or deleted_records:
                self._sync_to_mongodb(list(customers_dict.values()), deleted_records)
            
            self._save_sync_time(current_sync)
            
            logger.success(f"Sync completed successfully at {current_sync}")
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            raise
    
    def close(self):
        try:
            self.pg_conn.close()
            logger.info("Database connections closed")
        except:
            pass

def main():
    syncer = None
    try:
        syncer = DataSync()
        syncer.sync()
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise
    finally:
        if syncer:
            syncer.close()

if __name__ == "__main__":
    main()
