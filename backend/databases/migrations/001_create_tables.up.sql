-- Master Tables (INT PKs for readability)
CREATE TABLE product_status (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE product_condition (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE payment_method (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE shipping_method (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL
);

-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY,
  username VARCHAR(64) NOT NULL,
  password_hash TEXT NOT NULL,
  role VARCHAR(32) NOT NULL,
  email VARCHAR(128),
  profile_photo TEXT,
  last_login TIMESTAMP,
  created_by UUID,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_by UUID,
  updated_at TIMESTAMP DEFAULT NOW()
);

-- User Logs
CREATE TABLE user_logs (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  action TEXT NOT NULL,
  details TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Customers
CREATE TABLE customers (
  id UUID PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  phone VARCHAR(32),
  email VARCHAR(128),
  instagram VARCHAR(64),
  address_line1 TEXT,
  address_line2 TEXT,
  city VARCHAR(64),
  province VARCHAR(64),
  postal_code VARCHAR(15),
  country VARCHAR(64),
  notes TEXT,
  created_by UUID,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_by UUID,
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Products
CREATE TABLE products (
  id UUID PRIMARY KEY,
  code VARCHAR(32) UNIQUE NOT NULL, -- e.g., "LVNF0001"
  name TEXT NOT NULL,
  brand VARCHAR(64) NOT NULL,
  description TEXT,
  price NUMERIC(12,2),
  status_id INT REFERENCES product_status(id),
  condition_id INT REFERENCES product_condition(id),
  seller_id UUID REFERENCES customers(id),
  created_by UUID,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_by UUID,
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Product Images
CREATE TABLE product_images (
  id UUID PRIMARY KEY,
  product_id UUID REFERENCES products(id),
  url TEXT NOT NULL,
  is_primary BOOLEAN DEFAULT FALSE,
  created_by UUID,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_by UUID,
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Product Logs
CREATE TABLE product_logs (
  id UUID PRIMARY KEY,
  product_id UUID REFERENCES products(id),
  action TEXT NOT NULL,
  details TEXT,
  created_by UUID,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Transactions
CREATE TABLE transactions (
  id UUID PRIMARY KEY,
  customer_id UUID REFERENCES customers(id),
  sold_by_user_id UUID REFERENCES users(id),
  payment_method_id INT REFERENCES payment_method(id),
  shipping_method_id INT REFERENCES shipping_method(id),
  shipping_address_line1 TEXT,
  shipping_address_line2 TEXT,
  shipping_city VARCHAR(64),
  shipping_province VARCHAR(64),
  shipping_postal_code VARCHAR(15),
  shipping_country VARCHAR(64),
  shipped_at TIMESTAMP,
  arrived_at TIMESTAMP,
  delivered_at TIMESTAMP,
  shipping_fee NUMERIC(12,2) DEFAULT 0,
  total_price NUMERIC(12,2),
  notes TEXT,
  created_by UUID,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_by UUID,
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Transaction Details
CREATE TABLE transaction_details (
  id UUID PRIMARY KEY,
  transaction_id UUID REFERENCES transactions(id),
  product_id UUID REFERENCES products(id),
  price_at_sale NUMERIC(12,2),
  notes TEXT,
  created_by UUID,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_by UUID,
  updated_at TIMESTAMP DEFAULT NOW()
);
