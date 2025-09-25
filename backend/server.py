from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'luxtrack-super-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Create the main app without a prefix
app = FastAPI(title="LuxTrack MVP", description="Luxury Goods Inventory & Sales Tracking System")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"

class ProductCondition(str, Enum):
    EXCELLENT = "excellent"
    VERY_GOOD = "very_good"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

class ProductStatus(str, Enum):
    AVAILABLE = "available"
    SOLD = "sold"
    RESERVED = "reserved"
    DAMAGED = "damaged"
    UNDER_INSPECTION = "under_inspection"

class TransactionType(str, Enum):
    PURCHASE = "purchase"  # Buying from seller
    SALE = "sale"         # Selling to buyer

class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class SourceType(str, Enum):
    CONSIGNER = "consigner"
    ESTATE_SALE = "estate_sale"
    AUCTION = "auction"
    PRIVATE_SELLER = "private_seller"
    WHOLESALE = "wholesale"
    OTHER = "other"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.STAFF
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.STAFF

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Customer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CustomerCreate(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class Source(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    source_type: SourceType
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    commission_rate: Optional[float] = None  # For consigners
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SourceCreate(BaseModel):
    name: str
    source_type: SourceType
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    commission_rate: Optional[float] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    name: str
    brand: str
    category: str
    condition: ProductCondition
    status: ProductStatus = ProductStatus.AVAILABLE
    purchase_price: float
    selling_price: Optional[float] = None
    description: Optional[str] = None
    images: List[str] = []  # Base64 encoded images
    seller_id: Optional[str] = None  # Customer who sold to us (deprecated, use source_id)
    source_id: Optional[str] = None  # Source/Consigner who provided the product
    created_by: str  # User who created the record
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductCreate(BaseModel):
    code: str
    name: str
    brand: str
    category: str
    condition: ProductCondition
    purchase_price: float
    selling_price: Optional[float] = None
    description: Optional[str] = None
    images: List[str] = []
    seller_id: Optional[str] = None  # Keep for backward compatibility
    source_id: Optional[str] = None

class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_type: TransactionType
    status: TransactionStatus = TransactionStatus.PENDING
    customer_id: str  # Buyer for sales, Seller for purchases
    total_amount: float
    payment_method: str
    shipping_method: Optional[str] = None
    notes: Optional[str] = None
    arrival_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_by: str  # User who created the transaction
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TransactionItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_id: str
    product_id: str
    quantity: int = 1
    unit_price: float
    total_price: float

class TransactionCreate(BaseModel):
    transaction_type: TransactionType
    customer_id: str
    payment_method: str
    shipping_method: Optional[str] = None
    notes: Optional[str] = None
    items: List[Dict[str, Any]]  # [{product_id, quantity, unit_price}]

class ProductLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    action: str  # "created", "updated", "status_changed", "sold", etc.
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    user_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: User

# Utility Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_doc = await db.users.find_one({"id": user_id})
        if user_doc is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user_doc)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def log_product_action(product_id: str, action: str, user_id: str, old_value: Optional[Dict] = None, new_value: Optional[Dict] = None):
    log_entry = ProductLog(
        product_id=product_id,
        action=action,
        old_value=old_value,
        new_value=new_value,
        user_id=user_id
    )
    await db.product_logs.insert_one(log_entry.dict())

# Authentication Routes
@api_router.post("/auth/register", response_model=User)
async def register(user_create: UserCreate, current_user: User = Depends(get_admin_user)):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_create.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_dict = user_create.dict()
    user_dict['password'] = hash_password(user_create.password)
    user = User(**{k: v for k, v in user_dict.items() if k != 'password'})
    
    await db.users.insert_one({**user.dict(), 'password': user_dict['password']})
    return user

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_login: UserLogin):
    # Find user
    user_doc = await db.users.find_one({"email": user_login.email})
    if not user_doc or not verify_password(user_login.password, user_doc['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = User(**{k: v for k, v in user_doc.items() if k != 'password'})
    
    # Create tokens
    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token({"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user
    )

# User Routes
@api_router.get("/users/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(get_admin_user)):
    users = await db.users.find().to_list(length=None)
    return [User(**{k: v for k, v in user.items() if k != 'password'}) for user in users]

# Customer Routes
@api_router.post("/customers", response_model=Customer)
async def create_customer(customer_create: CustomerCreate, current_user: User = Depends(get_current_user)):
    customer = Customer(**customer_create.dict())
    await db.customers.insert_one(customer.dict())
    return customer

@api_router.get("/customers", response_model=List[Customer])
async def get_customers(current_user: User = Depends(get_current_user)):
    customers = await db.customers.find({"is_active": True}).to_list(length=None)
    return [Customer(**customer) for customer in customers]

@api_router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str, current_user: User = Depends(get_current_user)):
    customer_doc = await db.customers.find_one({"id": customer_id})
    if not customer_doc:
        raise HTTPException(status_code=404, detail="Customer not found")
    return Customer(**customer_doc)

@api_router.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, customer_create: CustomerCreate, current_user: User = Depends(get_current_user)):
    customer_doc = await db.customers.find_one({"id": customer_id})
    if not customer_doc:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    update_data = customer_create.dict()
    update_data['updated_at'] = datetime.now(timezone.utc)
    
    await db.customers.update_one({"id": customer_id}, {"$set": update_data})
    
    updated_customer = await db.customers.find_one({"id": customer_id})
    return Customer(**updated_customer)

# Source Routes
@api_router.post("/sources", response_model=Source)
async def create_source(source_create: SourceCreate, current_user: User = Depends(get_current_user)):
    source = Source(**source_create.dict())
    await db.sources.insert_one(source.dict())
    return source

@api_router.get("/sources", response_model=List[Source])
async def get_sources(current_user: User = Depends(get_current_user)):
    sources = await db.sources.find({"is_active": True}).to_list(length=None)
    return [Source(**source) for source in sources]

@api_router.get("/sources/{source_id}", response_model=Source)
async def get_source(source_id: str, current_user: User = Depends(get_current_user)):
    source_doc = await db.sources.find_one({"id": source_id})
    if not source_doc:
        raise HTTPException(status_code=404, detail="Source not found")
    return Source(**source_doc)

@api_router.put("/sources/{source_id}", response_model=Source)
async def update_source(source_id: str, source_create: SourceCreate, current_user: User = Depends(get_current_user)):
    source_doc = await db.sources.find_one({"id": source_id})
    if not source_doc:
        raise HTTPException(status_code=404, detail="Source not found")
    
    update_data = source_create.dict()
    update_data['updated_at'] = datetime.now(timezone.utc)
    
    await db.sources.update_one({"id": source_id}, {"$set": update_data})
    
    updated_source = await db.sources.find_one({"id": source_id})
    return Source(**updated_source)

# Product Routes
@api_router.post("/products", response_model=Product)
async def create_product(product_create: ProductCreate, current_user: User = Depends(get_current_user)):
    # Check if code already exists
    existing_product = await db.products.find_one({"code": product_create.code})
    if existing_product:
        raise HTTPException(status_code=400, detail="Product code already exists")
    
    product_dict = product_create.dict()
    product_dict['created_by'] = current_user.id
    product = Product(**product_dict)
    
    await db.products.insert_one(product.dict())
    
    # Log the creation
    await log_product_action(product.id, "created", current_user.id, new_value=product.dict())
    
    return product

@api_router.get("/products", response_model=List[Product])
async def get_products(current_user: User = Depends(get_current_user)):
    products = await db.products.find().to_list(length=None)
    return [Product(**product) for product in products]

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str, current_user: User = Depends(get_current_user)):
    product_doc = await db.products.find_one({"id": product_id})
    if not product_doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product_doc)

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_create: ProductCreate, current_user: User = Depends(get_current_user)):
    product_doc = await db.products.find_one({"id": product_id})
    if not product_doc:
        raise HTTPException(status_code=404, detail="Product not found")
    
    old_product = Product(**product_doc)
    
    update_data = product_create.dict()
    update_data['updated_at'] = datetime.now(timezone.utc)
    
    await db.products.update_one({"id": product_id}, {"$set": update_data})
    
    updated_product_doc = await db.products.find_one({"id": product_id})
    updated_product = Product(**updated_product_doc)
    
    # Log the update
    await log_product_action(product_id, "updated", current_user.id, old_value=old_product.dict(), new_value=updated_product.dict())
    
    return updated_product

@api_router.put("/products/{product_id}/status", response_model=Product)
async def update_product_status(product_id: str, status: ProductStatus, current_user: User = Depends(get_current_user)):
    product_doc = await db.products.find_one({"id": product_id})
    if not product_doc:
        raise HTTPException(status_code=404, detail="Product not found")
    
    old_status = product_doc['status']
    update_data = {
        'status': status,
        'updated_at': datetime.now(timezone.utc)
    }
    
    await db.products.update_one({"id": product_id}, {"$set": update_data})
    
    updated_product_doc = await db.products.find_one({"id": product_id})
    updated_product = Product(**updated_product_doc)
    
    # Log the status change
    await log_product_action(product_id, "status_changed", current_user.id, 
                           old_value={"status": old_status}, 
                           new_value={"status": status})
    
    return updated_product

# Transaction Routes
@api_router.post("/transactions", response_model=Transaction)
async def create_transaction(transaction_create: TransactionCreate, current_user: User = Depends(get_current_user)):
    # Verify customer exists
    customer_doc = await db.customers.find_one({"id": transaction_create.customer_id})
    if not customer_doc:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Calculate total amount and verify products
    total_amount = 0
    transaction_items = []
    
    for item_data in transaction_create.items:
        product_doc = await db.products.find_one({"id": item_data["product_id"]})
        if not product_doc:
            raise HTTPException(status_code=404, detail=f"Product {item_data['product_id']} not found")
        
        if product_doc['status'] != ProductStatus.AVAILABLE and transaction_create.transaction_type == TransactionType.SALE:
            raise HTTPException(status_code=400, detail=f"Product {product_doc['code']} is not available for sale")
        
        quantity = item_data.get("quantity", 1)
        unit_price = item_data["unit_price"]
        total_price = quantity * unit_price
        total_amount += total_price
        
        transaction_item = TransactionItem(
            product_id=item_data["product_id"],
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            transaction_id=""  # Will be set after transaction creation
        )
        transaction_items.append(transaction_item)
    
    # Create transaction
    transaction_dict = transaction_create.dict()
    transaction_dict['total_amount'] = total_amount
    transaction_dict['created_by'] = current_user.id
    transaction_dict.pop('items')  # Remove items from transaction dict
    
    transaction = Transaction(**transaction_dict)
    await db.transactions.insert_one(transaction.dict())
    
    # Create transaction items and update product statuses
    for item in transaction_items:
        item.transaction_id = transaction.id
        await db.transaction_items.insert_one(item.dict())
        
        # Update product status based on transaction type
        if transaction_create.transaction_type == TransactionType.SALE:
            await db.products.update_one(
                {"id": item.product_id}, 
                {"$set": {"status": ProductStatus.SOLD, "updated_at": datetime.now(timezone.utc)}}
            )
            await log_product_action(item.product_id, "sold", current_user.id, 
                                   new_value={"transaction_id": transaction.id})
    
    return transaction

@api_router.get("/transactions", response_model=List[Transaction])
async def get_transactions(current_user: User = Depends(get_current_user)):
    transactions = await db.transactions.find().to_list(length=None)
    return [Transaction(**transaction) for transaction in transactions]

@api_router.get("/transactions/{transaction_id}", response_model=Transaction)
async def get_transaction(transaction_id: str, current_user: User = Depends(get_current_user)):
    transaction_doc = await db.transactions.find_one({"id": transaction_id})
    if not transaction_doc:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return Transaction(**transaction_doc)

@api_router.get("/transactions/{transaction_id}/items", response_model=List[TransactionItem])
async def get_transaction_items(transaction_id: str, current_user: User = Depends(get_current_user)):
    items = await db.transaction_items.find({"transaction_id": transaction_id}).to_list(length=None)
    return [TransactionItem(**item) for item in items]

# Dashboard/Stats Routes
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    # Get counts
    total_products = await db.products.count_documents({})
    available_products = await db.products.count_documents({"status": ProductStatus.AVAILABLE})
    sold_products = await db.products.count_documents({"status": ProductStatus.SOLD})
    total_customers = await db.customers.count_documents({"is_active": True})
    total_sources = await db.sources.count_documents({"is_active": True})
    total_transactions = await db.transactions.count_documents({})
    
    # Get recent transactions
    recent_transactions = await db.transactions.find().sort("created_at", -1).limit(5).to_list(length=None)
    
    # Calculate revenue (completed sales only)
    sales_pipeline = [
        {"$match": {"transaction_type": TransactionType.SALE, "status": TransactionStatus.COMPLETED}},
        {"$group": {"_id": None, "total_revenue": {"$sum": "$total_amount"}}}
    ]
    
    revenue_result = await db.transactions.aggregate(sales_pipeline).to_list(length=None)
    total_revenue = revenue_result[0]['total_revenue'] if revenue_result else 0
    
    return {
        "total_products": total_products,
        "available_products": available_products,
        "sold_products": sold_products,
        "total_customers": total_customers,
        "total_sources": total_sources,
        "total_transactions": total_transactions,
        "total_revenue": total_revenue,
        "recent_transactions": [Transaction(**tx) for tx in recent_transactions]
    }

# Enhanced Detail Routes
@api_router.get("/products/{product_id}/details")
async def get_product_details(product_id: str, current_user: User = Depends(get_current_user)):
    # Get product
    product_doc = await db.products.find_one({"id": product_id})
    if not product_doc:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = Product(**product_doc)
    
    # Get source details if available
    source = None
    if product.source_id:
        source_doc = await db.sources.find_one({"id": product.source_id})
        if source_doc:
            source = Source(**source_doc)
    
    # Get seller details if available (backward compatibility)
    seller = None
    if product.seller_id:
        seller_doc = await db.customers.find_one({"id": product.seller_id})
        if seller_doc:
            seller = Customer(**seller_doc)
    
    # Get created by user
    creator_doc = await db.users.find_one({"id": product.created_by})
    creator = User(**{k: v for k, v in creator_doc.items() if k != 'password'}) if creator_doc else None
    
    # Get product logs
    logs = await db.product_logs.find({"product_id": product_id}).sort("timestamp", -1).to_list(length=None)
    product_logs = [ProductLog(**log) for log in logs]
    
    # Get transactions involving this product
    transaction_items = await db.transaction_items.find({"product_id": product_id}).to_list(length=None)
    transaction_ids = [item["transaction_id"] for item in transaction_items]
    
    transactions = []
    if transaction_ids:
        transaction_docs = await db.transactions.find({"id": {"$in": transaction_ids}}).to_list(length=None)
        transactions = [Transaction(**tx) for tx in transaction_docs]
    
    return {
        "product": product,
        "source": source,
        "seller": seller,  # For backward compatibility
        "creator": creator,
        "logs": product_logs,
        "transactions": transactions
    }

@api_router.get("/transactions/{transaction_id}/details")
async def get_transaction_details(transaction_id: str, current_user: User = Depends(get_current_user)):
    # Get transaction
    transaction_doc = await db.transactions.find_one({"id": transaction_id})
    if not transaction_doc:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    transaction = Transaction(**transaction_doc)
    
    # Get customer details
    customer_doc = await db.customers.find_one({"id": transaction.customer_id})
    customer = Customer(**customer_doc) if customer_doc else None
    
    # Get created by user
    creator_doc = await db.users.find_one({"id": transaction.created_by})
    creator = User(**{k: v for k, v in creator_doc.items() if k != 'password'}) if creator_doc else None
    
    # Get transaction items with product details
    transaction_items = await db.transaction_items.find({"transaction_id": transaction_id}).to_list(length=None)
    
    detailed_items = []
    for item_doc in transaction_items:
        item = TransactionItem(**item_doc)
        
        # Get product details for this item
        product_doc = await db.products.find_one({"id": item.product_id})
        product = Product(**product_doc) if product_doc else None
        
        detailed_items.append({
            "item": item,
            "product": product
        })
    
    return {
        "transaction": transaction,
        "customer": customer,
        "creator": creator,
        "items": detailed_items
    }

@api_router.get("/customers/{customer_id}/details")
async def get_customer_details(customer_id: str, current_user: User = Depends(get_current_user)):
    # Get customer
    customer_doc = await db.customers.find_one({"id": customer_id})
    if not customer_doc:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer = Customer(**customer_doc)
    
    # Get transactions for this customer
    transaction_docs = await db.transactions.find({"customer_id": customer_id}).sort("created_at", -1).to_list(length=None)
    transactions = [Transaction(**tx) for tx in transaction_docs]
    
    # Calculate totals
    total_purchases = sum(tx.total_amount for tx in transactions if tx.transaction_type == TransactionType.PURCHASE)
    total_sales = sum(tx.total_amount for tx in transactions if tx.transaction_type == TransactionType.SALE)
    
    return {
        "customer": customer,
        "transactions": transactions,
        "total_purchases": total_purchases,
        "total_sales": total_sales,
        "transaction_count": len(transactions)
    }

# Product Logs Route
@api_router.get("/products/{product_id}/logs", response_model=List[ProductLog])
async def get_product_logs(product_id: str, current_user: User = Depends(get_current_user)):
    logs = await db.product_logs.find({"product_id": product_id}).sort("timestamp", -1).to_list(length=None)
    return [ProductLog(**log) for log in logs]

# Health check route
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("LuxTrack MVP Server starting up...")
    
    # Create default admin user if none exists
    admin_count = await db.users.count_documents({"role": UserRole.ADMIN})
    if admin_count == 0:
        default_admin = {
            "id": str(uuid.uuid4()),
            "email": "admin@luxtrack.com",
            "password": hash_password("admin123"),
            "full_name": "System Administrator",
            "role": UserRole.ADMIN,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.users.insert_one(default_admin)
        logger.info("Default admin user created: admin@luxtrack.com / admin123")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()