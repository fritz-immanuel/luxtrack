# server_mysql.py
import os
import logging
import uuid
import traceback
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import bcrypt
import jwt

# SQL / async DB
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import JSON as SAJSON
from sqlalchemy import func, select, text
from databases import Database

from pydantic import BaseModel, Field, EmailStr
from enum import Enum

# -----------------------
# Load environment
# -----------------------
ROOT = os.path.dirname(__file__)
load_dotenv(os.path.join(ROOT, ".env"))

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
	# fallback local for dev:
	DATABASE_URL = "mysql+asyncmy://root:password@127.0.0.1:3306/luxtrack"

JWT_SECRET = os.getenv("JWT_SECRET", "luxtrack-super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# -----------------------
# Logging
# -----------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# -----------------------
# FastAPI app + router
# -----------------------
app = FastAPI(title="LuxTrack (MySQL)", description="LuxTrack MySQL-backed API")
api_router = APIRouter(prefix="/api")

# -----------------------
# CORS (same logic as you had)
# -----------------------
_raw = os.getenv("CORS_ORIGINS", "")
ALLOWED_ORIGINS = [o.strip() for o in _raw.split(",") if o.strip()]
if not ALLOWED_ORIGINS:
	logger.warning("CORS_ORIGINS empty; no cross-origin will be allowed")
else:
	logger.info("CORS allowed origins: %s", ALLOWED_ORIGINS)
if "*" in ALLOWED_ORIGINS:
	logger.warning('CORS_ORIGINS contains "*", removing to be safe with credentials')
	ALLOWED_ORIGINS = [o for o in ALLOWED_ORIGINS if o != "*"]
app.add_middleware(
	CORSMiddleware,
	allow_origins=ALLOWED_ORIGINS,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# -----------------------
# Database setup (databases + SQLAlchemy metadata)
# -----------------------
# Use databases package for async queries
database = Database(DATABASE_URL)

metadata = sa.MetaData()

# Users table
users = sa.Table(
	"users",
	metadata,
	sa.Column("id", sa.String(36), primary_key=True),
	sa.Column("email", sa.String(255), unique=True, nullable=False),
	sa.Column("password", sa.String(255), nullable=False),
	sa.Column("full_name", sa.String(255), nullable=False),
	sa.Column("role", sa.String(50), nullable=False, server_default="staff"),
	sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.sql.expression.true()),
	sa.Column("created_at", sa.DateTime, nullable=False),
	sa.Column("updated_at", sa.DateTime, nullable=False),
)

customers = sa.Table(
	"customers",
	metadata,
	sa.Column("id", sa.String(36), primary_key=True),
	sa.Column("full_name", sa.String(255), nullable=False),
	sa.Column("email", sa.String(255)),
	sa.Column("phone", sa.String(64)),
	sa.Column("address", sa.Text),
	sa.Column("notes", sa.Text),
	sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.sql.expression.true()),
	sa.Column("created_at", sa.DateTime, nullable=False),
	sa.Column("updated_at", sa.DateTime, nullable=False),
)

sources = sa.Table(
	"sources",
	metadata,
	sa.Column("id", sa.String(36), primary_key=True),
	sa.Column("name", sa.String(255), nullable=False),
	sa.Column("source_type", sa.String(64)),
	sa.Column("contact_person", sa.String(255)),
	sa.Column("email", sa.String(255)),
	sa.Column("phone", sa.String(64)),
	sa.Column("address", sa.Text),
	sa.Column("commission_rate", sa.Float),
	sa.Column("payment_terms", sa.String(255)),
	sa.Column("notes", sa.Text),
	sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.sql.expression.true()),
	sa.Column("created_at", sa.DateTime, nullable=False),
	sa.Column("updated_at", sa.DateTime, nullable=False),
)

products = sa.Table(
	"products",
	metadata,
	sa.Column("id", sa.String(36), primary_key=True),
	sa.Column("code", sa.String(100), unique=True, nullable=False),
	sa.Column("name", sa.String(255), nullable=False),
	sa.Column("brand", sa.String(255)),
	sa.Column("category", sa.String(255)),
	sa.Column("condition", sa.String(50)),
	sa.Column("status", sa.String(50)),
	sa.Column("purchase_price", sa.Float),
	sa.Column("selling_price", sa.Float),
	sa.Column("description", sa.Text),
	sa.Column("images", SAJSON),  # store array of image URLs/base64
	sa.Column("seller_id", sa.String(36)),
	sa.Column("source_id", sa.String(36)),
	sa.Column("created_by", sa.String(36)),
	sa.Column("created_at", sa.DateTime, nullable=False),
	sa.Column("updated_at", sa.DateTime, nullable=False),
)

transactions = sa.Table(
	"transactions",
	metadata,
	sa.Column("id", sa.String(36), primary_key=True),
	sa.Column("transaction_type", sa.String(50)),
	sa.Column("status", sa.String(50)),
	sa.Column("customer_id", sa.String(36)),
	sa.Column("total_amount", sa.Float),
	sa.Column("payment_method", sa.String(255)),
	sa.Column("shipping_method", sa.String(255)),
	sa.Column("notes", sa.Text),
	sa.Column("arrival_at", sa.DateTime),
	sa.Column("delivered_at", sa.DateTime),
	sa.Column("created_by", sa.String(36)),
	sa.Column("created_at", sa.DateTime, nullable=False),
	sa.Column("updated_at", sa.DateTime, nullable=False),
)

transaction_items = sa.Table(
	"transaction_items",
	metadata,
	sa.Column("id", sa.String(36), primary_key=True),
	sa.Column("transaction_id", sa.String(36), index=True),
	sa.Column("product_id", sa.String(36), index=True),
	sa.Column("quantity", sa.Integer),
	sa.Column("unit_price", sa.Float),
	sa.Column("total_price", sa.Float),
)

product_logs = sa.Table(
	"product_logs",
	metadata,
	sa.Column("id", sa.String(36), primary_key=True),
	sa.Column("product_id", sa.String(36), index=True),
	sa.Column("action", sa.String(100)),
	sa.Column("old_value", SAJSON),
	sa.Column("new_value", SAJSON),
	sa.Column("user_id", sa.String(36)),
	sa.Column("timestamp", sa.DateTime, nullable=False),
)

# -----------------------
# Pydantic schemas (reuse your existing ones)
# -----------------------
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
	PURCHASE = "purchase"
	SALE = "sale"

class TransactionStatus(str, Enum):
	PENDING = "pending"
	COMPLETED = "completed"
	CANCELLED = "cancelled"
	REFUNDED = "refunded"

# Keep your Pydantic models (copied / slightly trimmed)
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
	source_type: str
	contact_person: Optional[str] = None
	email: Optional[EmailStr] = None
	phone: Optional[str] = None
	address: Optional[str] = None
	commission_rate: Optional[float] = None
	payment_terms: Optional[str] = None
	notes: Optional[str] = None
	is_active: bool = True
	created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
	updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SourceCreate(BaseModel):
	name: str
	source_type: str
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
	images: List[str] = []
	seller_id: Optional[str] = None
	source_id: Optional[str] = None
	created_by: str
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
	seller_id: Optional[str] = None
	source_id: Optional[str] = None

class Transaction(BaseModel):
	id: str = Field(default_factory=lambda: str(uuid.uuid4()))
	transaction_type: TransactionType
	status: TransactionStatus = TransactionStatus.PENDING
	customer_id: str
	total_amount: float
	payment_method: str
	shipping_method: Optional[str] = None
	notes: Optional[str] = None
	arrival_at: Optional[datetime] = None
	delivered_at: Optional[datetime] = None
	created_by: str
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
	items: List[Dict[str, Any]]

class ProductLog(BaseModel):
	id: str = Field(default_factory=lambda: str(uuid.uuid4()))
	product_id: str
	action: str
	old_value: Optional[Dict[str, Any]] = None
	new_value: Optional[Dict[str, Any]] = None
	user_id: str
	timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TokenResponse(BaseModel):
	access_token: str
	refresh_token: str
	token_type: str = "bearer"
	user: User

# -----------------------
# Auth utilities (same as before)
# -----------------------
def hash_password(password: str) -> str:
	return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
	return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

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

security = HTTPBearer()

# -----------------------
# DB helpers
# -----------------------
async def get_user_by_id(user_id: str) -> Optional[dict]:
	query = users.select().where(users.c.id == user_id)
	return await database.fetch_one(query)

async def get_user_by_email(email: str) -> Optional[dict]:
	query = users.select().where(users.c.email == email)
	return await database.fetch_one(query)

async def create_product_log(entry: ProductLog):
	query = product_logs.insert().values(
		id=entry.id,
		product_id=entry.product_id,
		action=entry.action,
		old_value=entry.old_value,
		new_value=entry.new_value,
		user_id=entry.user_id,
		timestamp=entry.timestamp,
	)
	await database.execute(query)

# -----------------------
# Auth dependency
# -----------------------
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
	try:
		payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
		if payload.get("type") != "access":
			raise HTTPException(status_code=401, detail="Invalid token type")
		user_id = payload.get("sub")
		if not user_id:
			raise HTTPException(status_code=401, detail="Invalid token")
		row = await get_user_by_id(user_id)
		if not row:
			raise HTTPException(status_code=401, detail="User not found")
		# convert row to User pydantic
		row = dict(row)
		return User(**{k: v for k, v in row.items() if k != "password"})
	except jwt.ExpiredSignatureError:
		raise HTTPException(status_code=401, detail="Token expired")
	except jwt.JWTError:
		raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(current_user: User = Depends(get_current_user)):
	if current_user.role != UserRole.ADMIN:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
	return current_user

# -----------------------
# Routes (similar logic, but using SQL queries)
# -----------------------

# Auth: register (admin-only)
@api_router.post("/auth/register", response_model=User)
async def register(user_create: UserCreate, current_user: User = Depends(get_admin_user)):
	existing = await get_user_by_email(user_create.email)
	if existing:
		raise HTTPException(status_code=400, detail="Email already registered")
	uid = str(uuid.uuid4())
	now = datetime.now(timezone.utc)
	hashed = hash_password(user_create.password)
	query = users.insert().values(
		id=uid,
		email=user_create.email,
		password=hashed,
		full_name=user_create.full_name,
		role=user_create.role.value if hasattr(user_create.role, "value") else user_create.role,
		is_active=True,
		created_at=now,
		updated_at=now,
	)
	await database.execute(query)
	return User(id=uid, email=user_create.email, full_name=user_create.full_name, role=user_create.role, is_active=True, created_at=now, updated_at=now)

# Auth: login
@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_login: UserLogin):
	row = await get_user_by_email(user_login.email)
	if not row or not verify_password(user_login.password, row["password"]):
		raise HTTPException(status_code=401, detail="Invalid credentials")
	user = User(**{k:v for k,v in dict(row).items() if k != "password"})
	access_token = create_access_token({"sub": user.id})
	refresh_token = create_refresh_token({"sub": user.id})
	return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=user)

# Users
@api_router.get("/users/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
	return current_user

@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(get_admin_user)):
	rows = await database.fetch_all(users.select())
	results = []
	for r in rows:
		d = dict(r)
		results.append(User(**{k:v for k,v in d.items() if k != "password"}))
	return results

# Customers
@api_router.post("/customers", response_model=Customer)
async def create_customer(customer_create: CustomerCreate, current_user: User = Depends(get_current_user)):
	cid = str(uuid.uuid4())
	now = datetime.now(timezone.utc)
	query = customers.insert().values(id=cid, full_name=customer_create.full_name, email=customer_create.email, phone=customer_create.phone, address=customer_create.address, notes=customer_create.notes, is_active=True, created_at=now, updated_at=now)
	await database.execute(query)
	return Customer(id=cid, full_name=customer_create.full_name, email=customer_create.email, phone=customer_create.phone, address=customer_create.address, notes=customer_create.notes, created_at=now, updated_at=now)

@api_router.get("/customers", response_model=List[Customer])
async def get_customers(current_user: User = Depends(get_current_user)):
	rows = await database.fetch_all(customers.select().where(customers.c.is_active == True))
	return [Customer(**dict(r)) for r in rows]

@api_router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str, current_user: User = Depends(get_current_user)):
	r = await database.fetch_one(customers.select().where(customers.c.id == customer_id))
	if not r:
		raise HTTPException(status_code=404, detail="Customer not found")
	return Customer(**dict(r))

@api_router.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, customer_create: CustomerCreate, current_user: User = Depends(get_current_user)):
	r = await database.fetch_one(customers.select().where(customers.c.id == customer_id))
	if not r:
		raise HTTPException(status_code=404, detail="Customer not found")
	now = datetime.now(timezone.utc)
	query = customers.update().where(customers.c.id == customer_id).values(full_name=customer_create.full_name, email=customer_create.email, phone=customer_create.phone, address=customer_create.address, notes=customer_create.notes, updated_at=now)
	await database.execute(query)
	nr = await database.fetch_one(customers.select().where(customers.c.id == customer_id))
	return Customer(**dict(nr))

# Sources
@api_router.post("/sources", response_model=Source)
async def create_source(source_create: SourceCreate, current_user: User = Depends(get_current_user)):
	sid = str(uuid.uuid4()); now = datetime.now(timezone.utc)
	query = sources.insert().values(
		id=sid, name=source_create.name, source_type=source_create.source_type, contact_person=source_create.contact_person,
		email=source_create.email, phone=source_create.phone, address=source_create.address,
		commission_rate=source_create.commission_rate, payment_terms=source_create.payment_terms, notes=source_create.notes,
		is_active=True, created_at=now, updated_at=now
	)
	await database.execute(query)
	return Source(id=sid, name=source_create.name, source_type=source_create.source_type, contact_person=source_create.contact_person, email=source_create.email, phone=source_create.phone, address=source_create.address, commission_rate=source_create.commission_rate, payment_terms=source_create.payment_terms, notes=source_create.notes, created_at=now, updated_at=now)

@api_router.get("/sources", response_model=List[Source])
async def get_sources(current_user: User = Depends(get_current_user)):
	rows = await database.fetch_all(sources.select().where(sources.c.is_active == True))
	return [Source(**dict(r)) for r in rows]

@api_router.get("/sources/{source_id}", response_model=Source)
async def get_source(source_id: str, current_user: User = Depends(get_current_user)):
	r = await database.fetch_one(sources.select().where(sources.c.id == source_id))
	if not r:
		raise HTTPException(status_code=404, detail="Source not found")
	return Source(**dict(r))

@api_router.put("/sources/{source_id}", response_model=Source)
async def update_source(source_id: str, source_create: SourceCreate, current_user: User = Depends(get_current_user)):
	r = await database.fetch_one(sources.select().where(sources.c.id == source_id))
	if not r:
		raise HTTPException(status_code=404, detail="Source not found")
	now = datetime.now(timezone.utc)
	query = sources.update().where(sources.c.id == source_id).values(
		name=source_create.name, source_type=source_create.source_type, contact_person=source_create.contact_person,
		email=source_create.email, phone=source_create.phone, address=source_create.address,
		commission_rate=source_create.commission_rate, payment_terms=source_create.payment_terms, notes=source_create.notes,
		updated_at=now
	)
	await database.execute(query)
	nr = await database.fetch_one(sources.select().where(sources.c.id == source_id))
	return Source(**dict(nr))

# Products
@api_router.post("/products", response_model=Product)
async def create_product(product_create: ProductCreate, current_user: User = Depends(get_current_user)):
	existing = await database.fetch_one(products.select().where(products.c.code == product_create.code))
	if existing:
		raise HTTPException(status_code=400, detail="Product code already exists")
	pid = str(uuid.uuid4()); now = datetime.now(timezone.utc)
	product_vals = {
		"id": pid,
		"code": product_create.code,
		"name": product_create.name,
		"brand": product_create.brand,
		"category": product_create.category,
		"condition": product_create.condition.value if hasattr(product_create.condition,"value") else product_create.condition,
		"status": ProductStatus.AVAILABLE.value,
		"purchase_price": product_create.purchase_price,
		"selling_price": product_create.selling_price,
		"description": product_create.description,
		"images": product_create.images,
		"seller_id": product_create.seller_id,
		"source_id": product_create.source_id,
		"created_by": current_user.id,
		"created_at": now,
		"updated_at": now,
	}
	await database.execute(products.insert().values(**product_vals))
	# log creation
	await create_product_log(ProductLog(id=str(uuid.uuid4()), product_id=pid, action="created", new_value=product_vals, user_id=current_user.id, timestamp=now))
	return Product(**product_vals)

@api_router.get("/products", response_model=List[Product])
async def get_products(current_user: User = Depends(get_current_user)):
	rows = await database.fetch_all(products.select())
	return [Product(**dict(r)) for r in rows]

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str, current_user: User = Depends(get_current_user)):
	r = await database.fetch_one(products.select().where(products.c.id == product_id))
	if not r:
		raise HTTPException(status_code=404, detail="Product not found")
	return Product(**dict(r))

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_create: ProductCreate, current_user: User = Depends(get_current_user)):
	r = await database.fetch_one(products.select().where(products.c.id == product_id))
	if not r:
		raise HTTPException(status_code=404, detail="Product not found")
	old = dict(r)
	now = datetime.now(timezone.utc)
	update_vals = {
		"name": product_create.name,
		"brand": product_create.brand,
		"category": product_create.category,
		"condition": product_create.condition.value if hasattr(product_create.condition,"value") else product_create.condition,
		"purchase_price": product_create.purchase_price,
		"selling_price": product_create.selling_price,
		"description": product_create.description,
		"images": product_create.images,
		"seller_id": product_create.seller_id,
		"source_id": product_create.source_id,
		"updated_at": now,
	}
	await database.execute(products.update().where(products.c.id == product_id).values(**update_vals))
	nr = await database.fetch_one(products.select().where(products.c.id == product_id))
	await create_product_log(ProductLog(id=str(uuid.uuid4()), product_id=product_id, action="updated", old_value=old, new_value=dict(nr), user_id=current_user.id, timestamp=now))
	return Product(**dict(nr))

@api_router.put("/products/{product_id}/status", response_model=Product)
async def update_product_status(product_id: str, status: ProductStatus, current_user: User = Depends(get_current_user)):
	r = await database.fetch_one(products.select().where(products.c.id == product_id))
	if not r:
		raise HTTPException(status_code=404, detail="Product not found")
	old_status = r["status"]
	now = datetime.now(timezone.utc)
	await database.execute(products.update().where(products.c.id == product_id).values(status=status.value if hasattr(status,"value") else status, updated_at=now))
	nr = await database.fetch_one(products.select().where(products.c.id == product_id))
	await create_product_log(ProductLog(id=str(uuid.uuid4()), product_id=product_id, action="status_changed", old_value={"status": old_status}, new_value={"status": status}, user_id=current_user.id, timestamp=now))
	return Product(**dict(nr))

# Transactions
@api_router.post("/transactions", response_model=Transaction)
async def create_transaction(transaction_create: TransactionCreate, current_user: User = Depends(get_current_user)):
	# verify customer
	cust = await database.fetch_one(customers.select().where(customers.c.id == transaction_create.customer_id))
	if not cust:
		raise HTTPException(status_code=404, detail="Customer not found")
	# calculate totals and verify products
	total_amount = 0.0
	items_out = []
	now = datetime.now(timezone.utc)
	for item in transaction_create.items:
		prod = await database.fetch_one(products.select().where(products.c.id == item["product_id"]))
		if not prod:
			raise HTTPException(status_code=404, detail=f"Product {item['product_id']} not found")
		if prod["status"] != ProductStatus.AVAILABLE.value and transaction_create.transaction_type == TransactionType.SALE:
			raise HTTPException(status_code=400, detail=f"Product {prod['code']} is not available for sale")
		qty = item.get("quantity", 1)
		unit = item["unit_price"]
		total = qty * unit
		total_amount += total
		items_out.append({"id": str(uuid.uuid4()), "transaction_id": None, "product_id": item["product_id"], "quantity": qty, "unit_price": unit, "total_price": total})
	# create transaction
	txid = str(uuid.uuid4())
	tx_vals = {
		"id": txid,
		"transaction_type": transaction_create.transaction_type.value if hasattr(transaction_create.transaction_type,"value") else transaction_create.transaction_type,
		"status": TransactionStatus.PENDING.value,
		"customer_id": transaction_create.customer_id,
		"total_amount": total_amount,
		"payment_method": transaction_create.payment_method,
		"shipping_method": transaction_create.shipping_method,
		"notes": transaction_create.notes,
		"arrival_at": transaction_create.arrival_at,
		"delivered_at": transaction_create.delivered_at,
		"created_by": current_user.id,
		"created_at": now,
		"updated_at": now,
	}
	await database.execute(transactions.insert().values(**tx_vals))
	# insert items & update products
	for item in items_out:
		item["transaction_id"] = txid
		await database.execute(transaction_items.insert().values(**item))
		if transaction_create.transaction_type == TransactionType.SALE:
			await database.execute(products.update().where(products.c.id == item["product_id"]).values(status=ProductStatus.SOLD.value, updated_at=now))
			await create_product_log(ProductLog(id=str(uuid.uuid4()), product_id=item["product_id"], action="sold", new_value={"transaction_id": txid}, user_id=current_user.id, timestamp=now))
	return Transaction(**tx_vals)

@api_router.get("/transactions", response_model=List[Transaction])
async def get_transactions(current_user: User = Depends(get_current_user)):
	rows = await database.fetch_all(transactions.select())
	return [Transaction(**dict(r)) for r in rows]

@api_router.get("/transactions/{transaction_id}", response_model=Transaction)
async def get_transaction(transaction_id: str, current_user: User = Depends(get_current_user)):
	r = await database.fetch_one(transactions.select().where(transactions.c.id == transaction_id))
	if not r:
		raise HTTPException(status_code=404, detail="Transaction not found")
	return Transaction(**dict(r))

@api_router.get("/transactions/{transaction_id}/items", response_model=List[TransactionItem])
async def get_transaction_items(transaction_id: str, current_user: User = Depends(get_current_user)):
	rows = await database.fetch_all(transaction_items.select().where(transaction_items.c.transaction_id == transaction_id))
	return [TransactionItem(**dict(r)) for r in rows]

# Dashboard
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
	total_products = await database.fetch_one(select([func.count()]).select_from(products))
	available_products = await database.fetch_one(select([func.count()]).select_from(products).where(products.c.status == ProductStatus.AVAILABLE.value))
	sold_products = await database.fetch_one(select([func.count()]).select_from(products).where(products.c.status == ProductStatus.SOLD.value))
	total_customers = await database.fetch_one(select([func.count()]).select_from(customers).where(customers.c.is_active == True))
	total_sources = await database.fetch_one(select([func.count()]).select_from(sources).where(sources.c.is_active == True))
	total_transactions = await database.fetch_one(select([func.count()]).select_from(transactions))
	# revenue
	q = sa.select([sa.func.sum(transactions.c.total_amount)]).where(transactions.c.transaction_type == TransactionType.SALE.value).where(transactions.c.status == TransactionStatus.COMPLETED.value)
	total_revenue_row = await database.fetch_one(q)
	total_revenue = total_revenue_row[0] if total_revenue_row and total_revenue_row[0] is not None else 0
	recent = await database.fetch_all(transactions.select().order_by(transactions.c.created_at.desc()).limit(5))
	return {
		"total_products": int(total_products[0]) if total_products else 0,
		"available_products": int(available_products[0]) if available_products else 0,
		"sold_products": int(sold_products[0]) if sold_products else 0,
		"total_customers": int(total_customers[0]) if total_customers else 0,
		"total_sources": int(total_sources[0]) if total_sources else 0,
		"total_transactions": int(total_transactions[0]) if total_transactions else 0,
		"total_revenue": total_revenue,
		"recent_transactions": [Transaction(**dict(r)) for r in recent],
	}

# Enhanced detail routes similar to your original ones
@api_router.get("/products/{product_id}/details")
async def get_product_details(product_id: str, current_user: User = Depends(get_current_user)):
	r = await database.fetch_one(products.select().where(products.c.id == product_id))
	if not r:
		raise HTTPException(status_code=404, detail="Product not found")
	product = Product(**dict(r))
	source = None
	if product.source_id:
		s = await database.fetch_one(sources.select().where(sources.c.id == product.source_id))
		source = Source(**dict(s)) if s else None
	seller = None
	if product.seller_id:
		s = await database.fetch_one(customers.select().where(customers.c.id == product.seller_id))
		seller = Customer(**dict(s)) if s else None
	creator = None
	if product.created_by:
		cu = await database.fetch_one(users.select().where(users.c.id == product.created_by))
		if cu:
			creator = User(**{k:v for k,v in dict(cu).items() if k != "password"})
	logs = await database.fetch_all(product_logs.select().where(product_logs.c.product_id == product_id).order_by(product_logs.c.timestamp.desc()))
	product_logs_res = [ProductLog(**dict(l)) for l in logs]
	titems = await database.fetch_all(transaction_items.select().where(transaction_items.c.product_id == product_id))
	txids = [ti["transaction_id"] for ti in titems]
	transactions_res = []
	if txids:
		rows = await database.fetch_all(transactions.select().where(transactions.c.id.in_(txids)))
		transactions_res = [Transaction(**dict(r)) for r in rows]
	return {"product": product, "source": source, "seller": seller, "creator": creator, "logs": product_logs_res, "transactions": transactions_res}

@api_router.get("/transactions/{transaction_id}/details")
async def get_transaction_details(transaction_id: str, current_user: User = Depends(get_current_user)):
	tx = await database.fetch_one(transactions.select().where(transactions.c.id == transaction_id))
	if not tx:
		raise HTTPException(status_code=404, detail="Transaction not found")
	tx_obj = Transaction(**dict(tx))
	customer = None
	if tx_obj.customer_id:
		c = await database.fetch_one(customers.select().where(customers.c.id == tx_obj.customer_id))
		customer = Customer(**dict(c)) if c else None
	creator = None
	if tx_obj.created_by:
		cu = await database.fetch_one(users.select().where(users.c.id == tx_obj.created_by))
		creator = User(**{k:v for k,v in dict(cu).items() if k != "password"}) if cu else None
	items = await database.fetch_all(transaction_items.select().where(transaction_items.c.transaction_id == transaction_id))
	detailed = []
	for it in items:
		prod = await database.fetch_one(products.select().where(products.c.id == it["product_id"]))
		detailed.append({"item": TransactionItem(**dict(it)), "product": Product(**dict(prod)) if prod else None})
	return {"transaction": tx_obj, "customer": customer, "creator": creator, "items": detailed}

@api_router.get("/customers/{customer_id}/details")
async def get_customer_details(customer_id: str, current_user: User = Depends(get_current_user)):
	c = await database.fetch_one(customers.select().where(customers.c.id == customer_id))
	if not c:
		raise HTTPException(status_code=404, detail="Customer not found")
	cust = Customer(**dict(c))
	txs = await database.fetch_all(transactions.select().where(transactions.c.customer_id == customer_id).order_by(transactions.c.created_at.desc()))
	tx_objs = [Transaction(**dict(t)) for t in txs]
	total_purchases = sum(t.total_amount for t in tx_objs if t.transaction_type == TransactionType.PURCHASE)
	total_sales = sum(t.total_amount for t in tx_objs if t.transaction_type == TransactionType.SALE)
	return {"customer": cust, "transactions": tx_objs, "total_purchases": total_purchases, "total_sales": total_sales, "transaction_count": len(tx_objs)}

@api_router.get("/products/{product_id}/logs", response_model=List[ProductLog])
async def get_product_logs(product_id: str, current_user: User = Depends(get_current_user)):
	rows = await database.fetch_all(product_logs.select().where(product_logs.c.product_id == product_id).order_by(product_logs.c.timestamp.desc()))
	return [ProductLog(**dict(r)) for r in rows]

@api_router.get("/health")
async def health_check():
	return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

# include router
app.include_router(api_router)

# -----------------------
# Startup / shutdown handlers
# -----------------------
@app.on_event("startup")
async def startup():
	logger.info("Starting up MySQL-backed LuxTrack...")
	# connect DB
	await database.connect()
	# create default admin if none exists
	q = select([func.count()]).select_from(users).where(users.c.role == UserRole.ADMIN.value)
	res = await database.fetch_one(q)
	count = int(res[0]) if res and res[0] is not None else 0
	if count == 0:
		now = datetime.now(timezone.utc)
		uid = str(uuid.uuid4())
		hashed = hash_password("admin123")
		await database.execute(users.insert().values(id=uid, email="admin@luxtrack.com", password=hashed, full_name="System Administrator", role=UserRole.ADMIN.value, is_active=True, created_at=now, updated_at=now))
		logger.info("Created default admin user (admin@luxtrack.com / admin123)")

@app.on_event("shutdown")
async def shutdown():
	await database.disconnect()
	logger.info("Database disconnected")

# -----------------------
# Helper to create tables (dev only) - run once manually
# -----------------------
def create_tables_sync():
	"""
	Creates tables synchronously using a sync engine (requires PyMySQL).
	Run this once (locally or in an admin container) to bootstrap schema:
	  python -c "from server_mysql import create_tables_sync; create_tables_sync()"
	"""
	sync_url = DATABASE_URL
	# if using async driver in the URL (asyncmy), switch to pymysql for sync creation
	if "+asyncmy" in sync_url:
		sync_url = sync_url.replace("+asyncmy", "+pymysql")
	engine = sa.create_engine(sync_url, echo=False, pool_pre_ping=True)
	metadata.create_all(engine)
	logger.info("Tables created (sync)")

if __name__ == "__main__":
	# quick local test
	create_tables_sync()
	import uvicorn
	uvicorn.run("server_mysql:app", host="0.0.0.0", port=8000, reload=True)
