CREATE TABLE customers (
  id SERIAL PRIMARY KEY,
  name TEXT,
  city TEXT
);

CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name TEXT,
  category TEXT,
  unit_cost NUMERIC,
  unit_price NUMERIC
);

CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  created_at TIMESTAMP,
  customer_id INTEGER REFERENCES customers(id),
  total_amount NUMERIC,
  cost_of_goods NUMERIC,
  status TEXT
);

CREATE TABLE order_items (
  id SERIAL PRIMARY KEY,
  order_id INTEGER REFERENCES orders(id),
  product_id INTEGER REFERENCES products(id),
  quantity INTEGER,
  unit_price NUMERIC,
  unit_cost NUMERIC
);

CREATE TABLE inventory (
  product_id INTEGER REFERENCES products(id),
  warehouse TEXT,
  quantity INTEGER,
  PRIMARY KEY(product_id, warehouse)
);
