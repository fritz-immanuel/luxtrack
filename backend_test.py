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