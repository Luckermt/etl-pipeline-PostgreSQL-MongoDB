CREATE TABLE customers (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(150) UNIQUE NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW(),
    deleted_at  TIMESTAMP NULL
);

CREATE TABLE orders (
    id           SERIAL PRIMARY KEY,
    customer_id  INT REFERENCES customers(id) ON DELETE CASCADE,
    status       VARCHAR(50) DEFAULT 'pending',
    created_at   TIMESTAMP DEFAULT NOW(),
    updated_at   TIMESTAMP DEFAULT NOW(),
    deleted_at   TIMESTAMP NULL
);

CREATE TABLE products (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    price       NUMERIC(10, 2) NOT NULL,
    description TEXT,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW(),
    deleted_at  TIMESTAMP NULL
);

CREATE TABLE order_products (
    order_id    INT REFERENCES orders(id) ON DELETE CASCADE,
    product_id  INT REFERENCES products(id) ON DELETE CASCADE,
    quantity    INT NOT NULL DEFAULT 1,
    price_at_time NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY (order_id, product_id)
);

CREATE INDEX idx_customers_created ON customers(created_at);
CREATE INDEX idx_customers_updated ON customers(updated_at);
CREATE INDEX idx_customers_deleted ON customers(deleted_at);

CREATE INDEX idx_orders_created ON orders(created_at);
CREATE INDEX idx_orders_updated ON orders(updated_at);
CREATE INDEX idx_orders_deleted ON orders(deleted_at);
CREATE INDEX idx_orders_customer ON orders(customer_id);

CREATE INDEX idx_products_created ON products(created_at);
CREATE INDEX idx_products_updated ON products(updated_at);
CREATE INDEX idx_products_deleted ON products(deleted_at);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE USER sync_user WITH PASSWORD 'sync_password';
GRANT SELECT ON customers, orders, products, order_products TO sync_user;

CREATE OR REPLACE FUNCTION soft_delete_customer()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE customers SET deleted_at = NOW() WHERE id = OLD.id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER soft_delete_customer_trigger
BEFORE DELETE ON customers
FOR EACH ROW
EXECUTE FUNCTION soft_delete_customer();

CREATE OR REPLACE FUNCTION soft_delete_order()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE orders SET deleted_at = NOW() WHERE id = OLD.id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER soft_delete_order_trigger
BEFORE DELETE ON orders
FOR EACH ROW
EXECUTE FUNCTION soft_delete_order();

CREATE OR REPLACE FUNCTION soft_delete_product()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE products SET deleted_at = NOW() WHERE id = OLD.id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER soft_delete_product_trigger
BEFORE DELETE ON products
FOR EACH ROW
EXECUTE FUNCTION soft_delete_product();