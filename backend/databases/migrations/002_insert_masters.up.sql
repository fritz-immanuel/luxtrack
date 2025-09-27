-- Product Statuses
INSERT INTO product_status (id, name) VALUES
  (1, 'available'),
  (2, 'reserved'),
  (3, 'sold');

-- Product Conditions
INSERT INTO product_condition (id, name) VALUES
  (1, 'mint'),
  (2, 'very good'),
  (3, 'good'),
  (4, 'fair'),
  (5, 'worn');

-- Payment Methods
INSERT INTO payment_method (id, name) VALUES
  (1, 'cash'),
  (2, 'bank transfer'),
  (3, 'QRIS'),
  (4, 'credit card');

-- Shipping Methods
INSERT INTO shipping_method (id, name) VALUES
  (1, 'GoSend'),
  (2, 'JNE'),
  (3, 'J&T'),
  (4, 'SiCepat');

-- Insert one admin user (UUID must be fixed/generated in Go if you want real login)
INSERT INTO users (
  id, username, password_hash, role, email, created_at
) VALUES (
  '11111111-1111-1111-1111-111111111111',
  'admin',
  '$2a$12$REPLACE_WITH_HASH',
  'admin',
  'admin@luxtrack.com',
  NOW()
);
