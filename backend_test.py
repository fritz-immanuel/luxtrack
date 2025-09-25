#!/usr/bin/env python3
"""
LuxTrack MVP Backend API Test Suite
Tests all backend endpoints comprehensively
"""

import requests
import json
import uuid
from datetime import datetime
import sys
import os

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
        return None

BASE_URL = get_backend_url()
if not BASE_URL:
    print("ERROR: Could not get REACT_APP_BACKEND_URL from frontend/.env")
    sys.exit(1)

API_URL = f"{BASE_URL}/api"
print(f"Testing backend at: {API_URL}")

# Global variables for test data
auth_token = None
test_customer_id = None
test_product_id = None
test_transaction_id = None
test_source_id = None
admin_user_id = None

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name):
        self.passed += 1
        print(f"✅ {test_name}")
    
    def add_fail(self, test_name, error):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ {test_name}: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY: {self.passed}/{total} tests passed")
        if self.errors:
            print(f"\nFAILED TESTS:")
            for error in self.errors:
                print(f"  - {error}")
        print(f"{'='*60}")
        return self.failed == 0

results = TestResults()

def make_request(method, endpoint, data=None, headers=None, expected_status=200):
    """Make HTTP request with error handling"""
    url = f"{API_URL}{endpoint}"
    
    default_headers = {'Content-Type': 'application/json'}
    if headers:
        default_headers.update(headers)
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=default_headers)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=default_headers)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, headers=default_headers)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=default_headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code != expected_status:
            return None, f"Expected status {expected_status}, got {response.status_code}: {response.text}"
        
        return response.json() if response.content else {}, None
    
    except requests.exceptions.RequestException as e:
        return None, f"Request failed: {str(e)}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON response: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

def test_health_check():
    """Test health check endpoint"""
    data, error = make_request('GET', '/health')
    if error:
        results.add_fail("Health Check", error)
        return False
    
    if data.get('status') != 'healthy':
        results.add_fail("Health Check", "Status not healthy")
        return False
    
    results.add_pass("Health Check")
    return True

def test_authentication():
    """Test authentication system"""
    global auth_token, admin_user_id
    
    # Test login with default admin
    login_data = {
        "email": "admin@luxtrack.com",
        "password": "admin123"
    }
    
    data, error = make_request('POST', '/auth/login', login_data)
    if error:
        results.add_fail("Admin Login", error)
        return False
    
    # Verify response structure
    required_fields = ['access_token', 'refresh_token', 'token_type', 'user']
    for field in required_fields:
        if field not in data:
            results.add_fail("Admin Login", f"Missing field: {field}")
            return False
    
    if data['token_type'] != 'bearer':
        results.add_fail("Admin Login", f"Wrong token type: {data['token_type']}")
        return False
    
    # Store auth token and user ID for subsequent tests
    auth_token = data['access_token']
    admin_user_id = data['user']['id']
    
    results.add_pass("Admin Login")
    return True

def test_user_management():
    """Test user management endpoints"""
    global auth_token
    
    if not auth_token:
        results.add_fail("User Management", "No auth token available")
        return False
    
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    # Test get current user
    data, error = make_request('GET', '/users/me', headers=headers)
    if error:
        results.add_fail("Get Current User", error)
        return False
    
    if data['email'] != 'admin@luxtrack.com':
        results.add_fail("Get Current User", f"Wrong email: {data['email']}")
        return False
    
    results.add_pass("Get Current User")
    
    # Test get all users (admin only)
    data, error = make_request('GET', '/users', headers=headers)
    if error:
        results.add_fail("Get All Users", error)
        return False
    
    if not isinstance(data, list):
        results.add_fail("Get All Users", "Response is not a list")
        return False
    
    results.add_pass("Get All Users")
    
    # Test user registration (admin only)
    new_user_data = {
        "email": f"staff{uuid.uuid4().hex[:8]}@luxtrack.com",
        "password": "staff123",
        "full_name": "Test Staff Member",
        "role": "staff"
    }
    
    data, error = make_request('POST', '/auth/register', new_user_data, headers=headers)
    if error:
        results.add_fail("User Registration", error)
        return False
    
    if data['email'] != new_user_data['email']:
        results.add_fail("User Registration", f"Email mismatch: {data['email']}")
        return False
    
    results.add_pass("User Registration")
    return True

def test_customer_management():
    """Test customer CRUD operations"""
    global auth_token, test_customer_id
    
    if not auth_token:
        results.add_fail("Customer Management", "No auth token available")
        return False
    
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    # Test create customer
    customer_data = {
        "full_name": "Isabella Rodriguez",
        "email": "isabella.rodriguez@email.com",
        "phone": "+1-555-0123",
        "address": "123 Luxury Lane, Beverly Hills, CA 90210",
        "notes": "VIP customer, prefers Hermès and Chanel"
    }
    
    data, error = make_request('POST', '/customers', customer_data, headers=headers)
    if error:
        results.add_fail("Create Customer", error)
        return False
    
    test_customer_id = data['id']
    if data['full_name'] != customer_data['full_name']:
        results.add_fail("Create Customer", f"Name mismatch: {data['full_name']}")
        return False
    
    results.add_pass("Create Customer")
    
    # Test get all customers
    data, error = make_request('GET', '/customers', headers=headers)
    if error:
        results.add_fail("Get All Customers", error)
        return False
    
    if not isinstance(data, list):
        results.add_fail("Get All Customers", "Response is not a list")
        return False
    
    results.add_pass("Get All Customers")
    
    # Test get specific customer
    data, error = make_request('GET', f'/customers/{test_customer_id}', headers=headers)
    if error:
        results.add_fail("Get Customer by ID", error)
        return False
    
    if data['id'] != test_customer_id:
        results.add_fail("Get Customer by ID", f"ID mismatch: {data['id']}")
        return False
    
    results.add_pass("Get Customer by ID")
    
    # Test update customer
    update_data = {
        "full_name": "Isabella Rodriguez-Smith",
        "email": "isabella.rodriguez@email.com",
        "phone": "+1-555-0123",
        "address": "456 Updated Street, Beverly Hills, CA 90210",
        "notes": "VIP customer, updated address"
    }
    
    data, error = make_request('PUT', f'/customers/{test_customer_id}', update_data, headers=headers)
    if error:
        results.add_fail("Update Customer", error)
        return False
    
    if data['full_name'] != update_data['full_name']:
        results.add_fail("Update Customer", f"Name not updated: {data['full_name']}")
        return False
    
    results.add_pass("Update Customer")
    return True

def test_product_management():
    """Test product CRUD operations and status updates"""
    global auth_token, test_product_id
    
    if not auth_token:
        results.add_fail("Product Management", "No auth token available")
        return False
    
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    # Test create product
    product_data = {
        "code": f"LV-{uuid.uuid4().hex[:8].upper()}",
        "name": "Louis Vuitton Neverfull MM",
        "brand": "Louis Vuitton",
        "category": "Handbags",
        "condition": "excellent",
        "purchase_price": 1200.00,
        "selling_price": 1800.00,
        "description": "Classic monogram canvas with natural leather trim",
        "images": [],
        "seller_id": test_customer_id
    }
    
    data, error = make_request('POST', '/products', product_data, headers=headers)
    if error:
        results.add_fail("Create Product", error)
        return False
    
    test_product_id = data['id']
    if data['code'] != product_data['code']:
        results.add_fail("Create Product", f"Code mismatch: {data['code']}")
        return False
    
    results.add_pass("Create Product")
    
    # Test get all products
    data, error = make_request('GET', '/products', headers=headers)
    if error:
        results.add_fail("Get All Products", error)
        return False
    
    if not isinstance(data, list):
        results.add_fail("Get All Products", "Response is not a list")
        return False
    
    results.add_pass("Get All Products")
    
    # Test get specific product
    data, error = make_request('GET', f'/products/{test_product_id}', headers=headers)
    if error:
        results.add_fail("Get Product by ID", error)
        return False
    
    if data['id'] != test_product_id:
        results.add_fail("Get Product by ID", f"ID mismatch: {data['id']}")
        return False
    
    results.add_pass("Get Product by ID")
    
    # Test update product
    update_data = {
        "code": product_data['code'],
        "name": "Louis Vuitton Neverfull MM - Updated",
        "brand": "Louis Vuitton",
        "category": "Handbags",
        "condition": "very_good",
        "purchase_price": 1200.00,
        "selling_price": 1750.00,
        "description": "Updated description - Classic monogram canvas",
        "images": [],
        "seller_id": test_customer_id
    }
    
    data, error = make_request('PUT', f'/products/{test_product_id}', update_data, headers=headers)
    if error:
        results.add_fail("Update Product", error)
        return False
    
    if data['name'] != update_data['name']:
        results.add_fail("Update Product", f"Name not updated: {data['name']}")
        return False
    
    results.add_pass("Update Product")
    
    # Test update product status
    data, error = make_request('PUT', f'/products/{test_product_id}/status?status=reserved', headers=headers)
    if error:
        results.add_fail("Update Product Status", error)
        return False
    
    if data['status'] != 'reserved':
        results.add_fail("Update Product Status", f"Status not updated: {data['status']}")
        return False
    
    results.add_pass("Update Product Status")
    
    # Reset status to available for transaction test
    data, error = make_request('PUT', f'/products/{test_product_id}/status?status=available', headers=headers)
    if error:
        results.add_fail("Reset Product Status", error)
        return False
    
    results.add_pass("Reset Product Status")
    return True

def test_transaction_system():
    """Test transaction creation and management"""
    global auth_token, test_transaction_id, test_customer_id, test_product_id
    
    if not auth_token or not test_customer_id or not test_product_id:
        results.add_fail("Transaction System", "Missing required test data")
        return False
    
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    # Test create transaction (sale)
    transaction_data = {
        "transaction_type": "sale",
        "customer_id": test_customer_id,
        "payment_method": "Credit Card",
        "shipping_method": "Express Delivery",
        "notes": "Customer requested expedited shipping",
        "items": [
            {
                "product_id": test_product_id,
                "quantity": 1,
                "unit_price": 1750.00
            }
        ]
    }
    
    data, error = make_request('POST', '/transactions', transaction_data, headers=headers)
    if error:
        results.add_fail("Create Transaction", error)
        return False
    
    test_transaction_id = data['id']
    if data['customer_id'] != test_customer_id:
        results.add_fail("Create Transaction", f"Customer ID mismatch: {data['customer_id']}")
        return False
    
    if data['total_amount'] != 1750.00:
        results.add_fail("Create Transaction", f"Total amount mismatch: {data['total_amount']}")
        return False
    
    results.add_pass("Create Transaction")
    
    # Test get all transactions
    data, error = make_request('GET', '/transactions', headers=headers)
    if error:
        results.add_fail("Get All Transactions", error)
        return False
    
    if not isinstance(data, list):
        results.add_fail("Get All Transactions", "Response is not a list")
        return False
    
    results.add_pass("Get All Transactions")
    
    # Test get specific transaction
    data, error = make_request('GET', f'/transactions/{test_transaction_id}', headers=headers)
    if error:
        results.add_fail("Get Transaction by ID", error)
        return False
    
    if data['id'] != test_transaction_id:
        results.add_fail("Get Transaction by ID", f"ID mismatch: {data['id']}")
        return False
    
    results.add_pass("Get Transaction by ID")
    
    # Test get transaction items
    data, error = make_request('GET', f'/transactions/{test_transaction_id}/items', headers=headers)
    if error:
        results.add_fail("Get Transaction Items", error)
        return False
    
    if not isinstance(data, list) or len(data) == 0:
        results.add_fail("Get Transaction Items", "No transaction items found")
        return False
    
    if data[0]['product_id'] != test_product_id:
        results.add_fail("Get Transaction Items", f"Product ID mismatch: {data[0]['product_id']}")
        return False
    
    results.add_pass("Get Transaction Items")
    
    # Verify product status changed to sold
    product_data, error = make_request('GET', f'/products/{test_product_id}', headers=headers)
    if error:
        results.add_fail("Verify Product Status Change", error)
        return False
    
    if product_data['status'] != 'sold':
        results.add_fail("Verify Product Status Change", f"Status not updated to sold: {product_data['status']}")
        return False
    
    results.add_pass("Verify Product Status Change")
    return True

def test_dashboard_analytics():
    """Test dashboard statistics"""
    global auth_token
    
    if not auth_token:
        results.add_fail("Dashboard Analytics", "No auth token available")
        return False
    
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    data, error = make_request('GET', '/dashboard/stats', headers=headers)
    if error:
        results.add_fail("Dashboard Stats", error)
        return False
    
    # Verify required fields
    required_fields = [
        'total_products', 'available_products', 'sold_products',
        'total_customers', 'total_transactions', 'total_revenue',
        'recent_transactions'
    ]
    
    for field in required_fields:
        if field not in data:
            results.add_fail("Dashboard Stats", f"Missing field: {field}")
            return False
    
    # Verify data types
    if not isinstance(data['recent_transactions'], list):
        results.add_fail("Dashboard Stats", "recent_transactions is not a list")
        return False
    
    # Verify we have at least one product and transaction from our tests
    if data['total_products'] < 1:
        results.add_fail("Dashboard Stats", f"Expected at least 1 product, got {data['total_products']}")
        return False
    
    if data['total_transactions'] < 1:
        results.add_fail("Dashboard Stats", f"Expected at least 1 transaction, got {data['total_transactions']}")
        return False
    
    results.add_pass("Dashboard Stats")
    return True

def test_audit_logging():
    """Test product audit logs"""
    global auth_token, test_product_id
    
    if not auth_token or not test_product_id:
        results.add_fail("Audit Logging", "Missing required test data")
        return False
    
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    data, error = make_request('GET', f'/products/{test_product_id}/logs', headers=headers)
    if error:
        results.add_fail("Product Logs", error)
        return False
    
    if not isinstance(data, list):
        results.add_fail("Product Logs", "Response is not a list")
        return False
    
    # We should have logs for: created, updated, status_changed (multiple times), sold
    if len(data) < 3:
        results.add_fail("Product Logs", f"Expected at least 3 log entries, got {len(data)}")
        return False
    
    # Verify log structure
    for log in data:
        required_fields = ['id', 'product_id', 'action', 'user_id', 'timestamp']
        for field in required_fields:
            if field not in log:
                results.add_fail("Product Logs", f"Missing field in log: {field}")
                return False
    
    results.add_pass("Product Logs")
    return True

def test_sources_management():
    """Test sources/consigners CRUD operations"""
    global auth_token, test_source_id
    
    if not auth_token:
        results.add_fail("Sources Management", "No auth token available")
        return False
    
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    # Test create source (consigner)
    source_data = {
        "name": "Elite Consignments Beverly Hills",
        "source_type": "consigner",
        "contact_person": "Margaret Thompson",
        "email": "margaret@eliteconsignments.com",
        "phone": "+1-310-555-0199",
        "address": "9876 Rodeo Drive, Beverly Hills, CA 90210",
        "commission_rate": 0.40,
        "payment_terms": "Net 30 days",
        "notes": "High-end luxury consigner, specializes in Hermès and Chanel"
    }
    
    data, error = make_request('POST', '/sources', source_data, headers=headers)
    if error:
        results.add_fail("Create Source (Consigner)", error)
        return False
    
    test_source_id = data['id']
    if data['name'] != source_data['name']:
        results.add_fail("Create Source (Consigner)", f"Name mismatch: {data['name']}")
        return False
    
    if data['source_type'] != source_data['source_type']:
        results.add_fail("Create Source (Consigner)", f"Source type mismatch: {data['source_type']}")
        return False
    
    results.add_pass("Create Source (Consigner)")
    
    # Test create estate sale source
    estate_source_data = {
        "name": "Malibu Estate Sale Co.",
        "source_type": "estate_sale",
        "contact_person": "Robert Wilson",
        "email": "robert@malibuestates.com",
        "phone": "+1-310-555-0288",
        "address": "12345 Pacific Coast Highway, Malibu, CA 90265",
        "payment_terms": "Payment on delivery",
        "notes": "Specializes in high-end estate liquidations"
    }
    
    data, error = make_request('POST', '/sources', estate_source_data, headers=headers)
    if error:
        results.add_fail("Create Source (Estate Sale)", error)
        return False
    
    results.add_pass("Create Source (Estate Sale)")
    
    # Test create auction source
    auction_source_data = {
        "name": "Christie's Beverly Hills",
        "source_type": "auction",
        "contact_person": "Sarah Mitchell",
        "email": "sarah.mitchell@christies.com",
        "phone": "+1-310-555-0377",
        "address": "9830 Wilshire Blvd, Beverly Hills, CA 90212",
        "payment_terms": "Immediate payment required",
        "notes": "Premier auction house for luxury goods"
    }
    
    data, error = make_request('POST', '/sources', auction_source_data, headers=headers)
    if error:
        results.add_fail("Create Source (Auction)", error)
        return False
    
    results.add_pass("Create Source (Auction)")
    
    # Test get all sources
    data, error = make_request('GET', '/sources', headers=headers)
    if error:
        results.add_fail("Get All Sources", error)
        return False
    
    if not isinstance(data, list):
        results.add_fail("Get All Sources", "Response is not a list")
        return False
    
    if len(data) < 3:
        results.add_fail("Get All Sources", f"Expected at least 3 sources, got {len(data)}")
        return False
    
    results.add_pass("Get All Sources")
    
    # Test get specific source
    data, error = make_request('GET', f'/sources/{test_source_id}', headers=headers)
    if error:
        results.add_fail("Get Source by ID", error)
        return False
    
    if data['id'] != test_source_id:
        results.add_fail("Get Source by ID", f"ID mismatch: {data['id']}")
        return False
    
    results.add_pass("Get Source by ID")
    
    # Test update source
    update_data = {
        "name": "Elite Consignments Beverly Hills - Updated",
        "source_type": "consigner",
        "contact_person": "Margaret Thompson-Smith",
        "email": "margaret@eliteconsignments.com",
        "phone": "+1-310-555-0199",
        "address": "9876 Rodeo Drive, Suite 200, Beverly Hills, CA 90210",
        "commission_rate": 0.35,
        "payment_terms": "Net 15 days",
        "notes": "Updated terms - High-end luxury consigner"
    }
    
    data, error = make_request('PUT', f'/sources/{test_source_id}', update_data, headers=headers)
    if error:
        results.add_fail("Update Source", error)
        return False
    
    if data['name'] != update_data['name']:
        results.add_fail("Update Source", f"Name not updated: {data['name']}")
        return False
    
    if data['commission_rate'] != update_data['commission_rate']:
        results.add_fail("Update Source", f"Commission rate not updated: {data['commission_rate']}")
        return False
    
    results.add_pass("Update Source")
    return True

def test_enhanced_product_management():
    """Test enhanced product management with source integration and multiple images"""
    global auth_token, test_product_id, test_source_id
    
    if not auth_token or not test_source_id:
        results.add_fail("Enhanced Product Management", "Missing required test data")
        return False
    
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    # Test create product with source_id and multiple images
    product_data = {
        "code": f"HER-{uuid.uuid4().hex[:8].upper()}",
        "name": "Hermès Birkin 35cm Togo Leather",
        "brand": "Hermès",
        "category": "Handbags",
        "condition": "excellent",
        "purchase_price": 8500.00,
        "selling_price": 12500.00,
        "description": "Authentic Hermès Birkin 35cm in Etoupe Togo leather with palladium hardware",
        "images": [
            "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
        ],
        "source_id": test_source_id
    }
    
    data, error = make_request('POST', '/products', product_data, headers=headers)
    if error:
        results.add_fail("Create Product with Source", error)
        return False
    
    test_product_id = data['id']
    if data['code'] != product_data['code']:
        results.add_fail("Create Product with Source", f"Code mismatch: {data['code']}")
        return False
    
    if data['source_id'] != test_source_id:
        results.add_fail("Create Product with Source", f"Source ID mismatch: {data['source_id']}")
        return False
    
    if len(data['images']) != 2:
        results.add_fail("Create Product with Source", f"Expected 2 images, got {len(data['images'])}")
        return False
    
    results.add_pass("Create Product with Source")
    
    # Test update product with new images
    update_data = {
        "code": product_data['code'],
        "name": "Hermès Birkin 35cm Togo Leather - Authenticated",
        "brand": "Hermès",
        "category": "Handbags",
        "condition": "excellent",
        "purchase_price": 8500.00,
        "selling_price": 13000.00,
        "description": "Updated - Authentic Hermès Birkin with authentication certificate",
        "images": [
            "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
        ],
        "source_id": test_source_id
    }
    
    data, error = make_request('PUT', f'/products/{test_product_id}', update_data, headers=headers)
    if error:
        results.add_fail("Update Product with Images", error)
        return False
    
    if data['name'] != update_data['name']:
        results.add_fail("Update Product with Images", f"Name not updated: {data['name']}")
        return False
    
    if len(data['images']) != 3:
        results.add_fail("Update Product with Images", f"Expected 3 images, got {len(data['images'])}")
        return False
    
    results.add_pass("Update Product with Images")
    return True

def test_enhanced_detail_endpoints():
    """Test enhanced detail endpoints for products, customers, and transactions"""
    global auth_token, test_product_id, test_customer_id, test_transaction_id, test_source_id
    
    if not auth_token or not test_product_id or not test_customer_id:
        results.add_fail("Enhanced Detail Endpoints", "Missing required test data")
        return False
    
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    # Test enhanced product details endpoint
    data, error = make_request('GET', f'/products/{test_product_id}/details', headers=headers)
    if error:
        results.add_fail("Product Details Endpoint", error)
        return False
    
    # Verify response structure
    required_fields = ['product', 'source', 'creator', 'logs', 'transactions']
    for field in required_fields:
        if field not in data:
            results.add_fail("Product Details Endpoint", f"Missing field: {field}")
            return False
    
    # Verify product data
    if data['product']['id'] != test_product_id:
        results.add_fail("Product Details Endpoint", f"Product ID mismatch: {data['product']['id']}")
        return False
    
    # Verify source data is included
    if data['source'] and data['source']['id'] != test_source_id:
        results.add_fail("Product Details Endpoint", f"Source ID mismatch: {data['source']['id']}")
        return False
    
    # Verify creator data
    if not data['creator'] or 'id' not in data['creator']:
        results.add_fail("Product Details Endpoint", "Creator data missing or invalid")
        return False
    
    # Verify logs are present
    if not isinstance(data['logs'], list):
        results.add_fail("Product Details Endpoint", "Logs should be a list")
        return False
    
    results.add_pass("Product Details Endpoint")
    
    # Test enhanced customer details endpoint
    data, error = make_request('GET', f'/customers/{test_customer_id}/details', headers=headers)
    if error:
        results.add_fail("Customer Details Endpoint", error)
        return False
    
    # Verify response structure
    required_fields = ['customer', 'transactions', 'total_purchases', 'total_sales', 'transaction_count']
    for field in required_fields:
        if field not in data:
            results.add_fail("Customer Details Endpoint", f"Missing field: {field}")
            return False
    
    # Verify customer data
    if data['customer']['id'] != test_customer_id:
        results.add_fail("Customer Details Endpoint", f"Customer ID mismatch: {data['customer']['id']}")
        return False
    
    # Verify transactions list
    if not isinstance(data['transactions'], list):
        results.add_fail("Customer Details Endpoint", "Transactions should be a list")
        return False
    
    # Verify totals are numbers
    if not isinstance(data['total_purchases'], (int, float)):
        results.add_fail("Customer Details Endpoint", "total_purchases should be a number")
        return False
    
    if not isinstance(data['total_sales'], (int, float)):
        results.add_fail("Customer Details Endpoint", "total_sales should be a number")
        return False
    
    results.add_pass("Customer Details Endpoint")
    
    # Create a transaction first if we don't have one
    if not test_transaction_id:
        # Reset product status to available for transaction
        make_request('PUT', f'/products/{test_product_id}/status?status=available', headers=headers)
        
        transaction_data = {
            "transaction_type": "sale",
            "customer_id": test_customer_id,
            "payment_method": "Credit Card",
            "shipping_method": "Express Delivery",
            "notes": "Test transaction for enhanced details",
            "items": [
                {
                    "product_id": test_product_id,
                    "quantity": 1,
                    "unit_price": 13000.00
                }
            ]
        }
        
        tx_data, tx_error = make_request('POST', '/transactions', transaction_data, headers=headers)
        if tx_error:
            results.add_fail("Create Transaction for Details Test", tx_error)
            return False
        
        test_transaction_id = tx_data['id']
    
    # Test enhanced transaction details endpoint
    data, error = make_request('GET', f'/transactions/{test_transaction_id}/details', headers=headers)
    if error:
        results.add_fail("Transaction Details Endpoint", error)
        return False
    
    # Verify response structure
    required_fields = ['transaction', 'customer', 'creator', 'items']
    for field in required_fields:
        if field not in data:
            results.add_fail("Transaction Details Endpoint", f"Missing field: {field}")
            return False
    
    # Verify transaction data
    if data['transaction']['id'] != test_transaction_id:
        results.add_fail("Transaction Details Endpoint", f"Transaction ID mismatch: {data['transaction']['id']}")
        return False
    
    # Verify customer data
    if not data['customer'] or data['customer']['id'] != test_customer_id:
        results.add_fail("Transaction Details Endpoint", "Customer data missing or invalid")
        return False
    
    # Verify creator data
    if not data['creator'] or 'id' not in data['creator']:
        results.add_fail("Transaction Details Endpoint", "Creator data missing or invalid")
        return False
    
    # Verify items with product details
    if not isinstance(data['items'], list) or len(data['items']) == 0:
        results.add_fail("Transaction Details Endpoint", "Items should be a non-empty list")
        return False
    
    # Check first item structure
    first_item = data['items'][0]
    if 'item' not in first_item or 'product' not in first_item:
        results.add_fail("Transaction Details Endpoint", "Item should contain 'item' and 'product' fields")
        return False
    
    results.add_pass("Transaction Details Endpoint")
    return True

def test_updated_dashboard():
    """Test updated dashboard with sources count"""
    global auth_token
    
    if not auth_token:
        results.add_fail("Updated Dashboard", "No auth token available")
        return False
    
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    data, error = make_request('GET', '/dashboard/stats', headers=headers)
    if error:
        results.add_fail("Updated Dashboard Stats", error)
        return False
    
    # Verify required fields including new total_sources
    required_fields = [
        'total_products', 'available_products', 'sold_products',
        'total_customers', 'total_sources', 'total_transactions', 
        'total_revenue', 'recent_transactions'
    ]
    
    for field in required_fields:
        if field not in data:
            results.add_fail("Updated Dashboard Stats", f"Missing field: {field}")
            return False
    
    # Verify total_sources is present and is a number
    if not isinstance(data['total_sources'], int):
        results.add_fail("Updated Dashboard Stats", f"total_sources should be an integer, got {type(data['total_sources'])}")
        return False
    
    # We should have at least 3 sources from our tests
    if data['total_sources'] < 3:
        results.add_fail("Updated Dashboard Stats", f"Expected at least 3 sources, got {data['total_sources']}")
        return False
    
    # Verify other fields are still working
    if not isinstance(data['recent_transactions'], list):
        results.add_fail("Updated Dashboard Stats", "recent_transactions is not a list")
        return False
    
    # Verify we have data from our tests
    if data['total_products'] < 1:
        results.add_fail("Updated Dashboard Stats", f"Expected at least 1 product, got {data['total_products']}")
        return False
    
    if data['total_customers'] < 1:
        results.add_fail("Updated Dashboard Stats", f"Expected at least 1 customer, got {data['total_customers']}")
        return False
    
    results.add_pass("Updated Dashboard Stats")
    return True

def test_error_handling():
    """Test error handling and validation"""
    global auth_token
    
    if not auth_token:
        results.add_fail("Error Handling", "No auth token available")
        return False
    
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    # Test invalid customer ID
    data, error = make_request('GET', '/customers/invalid-id', headers=headers, expected_status=404)
    if error and "Expected status 404" not in error:
        results.add_fail("Error Handling - Invalid Customer ID", error)
        return False
    
    results.add_pass("Error Handling - Invalid Customer ID")
    
    # Test invalid product ID
    data, error = make_request('GET', '/products/invalid-id', headers=headers, expected_status=404)
    if error and "Expected status 404" not in error:
        results.add_fail("Error Handling - Invalid Product ID", error)
        return False
    
    results.add_pass("Error Handling - Invalid Product ID")
    
    # Test unauthorized access (no token)
    data, error = make_request('GET', '/users/me', expected_status=403)
    if error and "Expected status 403" not in error:
        results.add_fail("Error Handling - Unauthorized Access", error)
        return False
    
    results.add_pass("Error Handling - Unauthorized Access")
    
    # Test duplicate product code
    unique_code = f"DUPLICATE-{uuid.uuid4().hex[:8].upper()}"
    duplicate_product = {
        "code": unique_code,
        "name": "Test Product",
        "brand": "Test Brand",
        "category": "Test Category",
        "condition": "excellent",
        "purchase_price": 100.00
    }
    
    # Create first product
    data, error = make_request('POST', '/products', duplicate_product, headers=headers)
    if error:
        results.add_fail("Error Handling - Create First Product", error)
        return False
    
    # Try to create duplicate
    data, error = make_request('POST', '/products', duplicate_product, headers=headers, expected_status=400)
    if error and "Expected status 400" not in error:
        results.add_fail("Error Handling - Duplicate Product Code", error)
        return False
    
    results.add_pass("Error Handling - Duplicate Product Code")
    return True

def main():
    """Run all tests"""
    print("🚀 Starting LuxTrack MVP Backend API Tests")
    print(f"Backend URL: {API_URL}")
    print("="*60)
    
    # Run tests in order
    test_functions = [
        test_health_check,
        test_authentication,
        test_user_management,
        test_customer_management,
        test_product_management,
        test_transaction_system,
        test_dashboard_analytics,
        test_audit_logging,
        test_error_handling
    ]
    
    for test_func in test_functions:
        try:
            test_func()
        except Exception as e:
            results.add_fail(test_func.__name__, f"Unexpected error: {str(e)}")
    
    # Print summary
    success = results.summary()
    
    if success:
        print("\n🎉 All tests passed! Backend API is working correctly.")
        return 0
    else:
        print(f"\n💥 {results.failed} tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())