import psycopg2
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

NUM_CUSTOMERS = 100000
MAX_ORDERS_PER_CUSTOMER = 10
NUM_PRODUCTS = 1000

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    database=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD')
)
conn.autocommit = False
cursor = conn.cursor()

def generate_products():
    """Генерация продуктов"""
    products = []
    categories = ['Электроника', 'Одежда', 'Книги', 'Дом', 'Спорт']
    
    for i in range(NUM_PRODUCTS):
        name = f"Продукт {i+1}"
        price = round(random.uniform(100, 100000), 2)
        category = random.choice(categories)
        description = f"Описание для {name}, категория: {category}"
        products.append((name, price, description))
    
    return products

def generate_customer_data():
    """Генерация данных покупателей и заказов"""
    try:
        logger.info("Генерация продуктов...")
        products = generate_products()
        
        product_ids = []
        for i in range(0, len(products), 1000):
            batch = products[i:i+1000]
            args_str = ','.join(cursor.mogrify("(%s,%s,%s)", p).decode() for p in batch)
            cursor.execute(f"INSERT INTO products (name, price, description) VALUES {args_str} RETURNING id")
            product_ids.extend([row[0] for row in cursor.fetchall()])
        
        conn.commit()
        logger.success(f"Создано {len(product_ids)} продуктов")
        
        logger.info("Генерация покупателей...")
        customers_data = []
        for i in range(NUM_CUSTOMERS):
            name = f"Пользователь {i+1}"
            email = f"user{i+1}@example.com"
            created_at = datetime.now() - timedelta(days=random.randint(0, 365))
            customers_data.append((name, email, created_at))
        
        customer_ids = []
        for i in range(0, len(customers_data), 1000):
            batch = customers_data[i:i+1000]
            args_str = ','.join(cursor.mogrify("(%s,%s,%s)", c).decode() for c in batch)
            cursor.execute(f"INSERT INTO customers (name, email, created_at) VALUES {args_str} RETURNING id")
            customer_ids.extend([row[0] for row in cursor.fetchall()])
        
        conn.commit()
        logger.success(f"Создано {len(customer_ids)} покупателей")
        
        logger.info("Генерация заказов...")
        statuses = ['pending', 'processing', 'completed', 'cancelled']
        
        for customer_id in customer_ids:
            num_orders = random.randint(0, MAX_ORDERS_PER_CUSTOMER)
            
            for _ in range(num_orders):
                status = random.choice(statuses)
                created_at = datetime.now() - timedelta(days=random.randint(0, 365))
                
                cursor.execute("""
                    INSERT INTO orders (customer_id, status, created_at)
                    VALUES (%s, %s, %s) RETURNING id
                """, (customer_id, status, created_at))
                
                order_id = cursor.fetchone()[0]
                
                num_products_in_order = random.randint(1, 5)
                selected_products = random.sample(product_ids, min(num_products_in_order, len(product_ids)))
                
                for product_id in selected_products:
                    quantity = random.randint(1, 3)
                    cursor.execute("SELECT price FROM products WHERE id = %s", (product_id,))
                    price = cursor.fetchone()[0]
                    
                    cursor.execute("""
                        INSERT INTO order_products (order_id, product_id, quantity, price_at_time)
                        VALUES (%s, %s, %s, %s)
                    """, (order_id, product_id, quantity, price))
            
            if customer_id % 1000 == 0:
                conn.commit()
                logger.info(f"Обработано {customer_id} покупателей...")
        
        conn.commit()
        logger.success("Генерация данных завершена успешно!")
        
        cursor.execute("SELECT COUNT(*) FROM customers")
        customers_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM orders")
        orders_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM order_products")
        order_products_count = cursor.fetchone()[0]
        
        logger.info(f"Статистика: {customers_count} покупателей, {orders_count} заказов, {order_products_count} связей заказ-продукт")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при генерации данных: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    generate_customer_data()