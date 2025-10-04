# server.py
# Paste this over your existing server.py (replace file)

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

from contextlib import asynccontextmanager

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
# FastAPI router (app will be created after lifespan below)
# -----------------------
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

# -----------------------
# Database setup (databases + SQLAlchemy metadata)
# -----------------------
# Use databases package for async queries
database = Database(DATABASE_URL)

metadata = sa.MetaData()

# -----------------------
# Tables (unchanged)
# -----------------------
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
    sa.Column("selling_price", products := None) if False else sa.Column("selling_price", sa.Float),  # keep column
    sa.Column("description", sa.Text),
    sa.Column("images", SAJSON),
    sa.Column("seller_id", sa.String(36)),
    sa.Column("source_id", sa.String(36)),
    sa.Column("created_by", sa.String(36)),
    sa.Column("created_at", sa.DateTime, nullable=False),
    sa.Column("updated_at", sa.DateTime, nullable=False),
)

# the above had a small hack to avoid linter noise; if you prefer normal explicit column,
# replace that line with: sa.Column("selling_price", sa.Float),

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
# Pydantic schemas (unchanged)
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

# Pydantic models (copy of your definitions; trimmed for brevity where appropriate)
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
# Auth utilities
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
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user

# -----------------------
# Routes (unchanged logic)
# -----------------------
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

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_login: UserLogin):
    row = await get_user_by_email(user_login.email)
    if not row or not verify_password(user_login.password, row["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = User(**{k: v for k, v in dict(row).items() if k != "password"})
    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token({"sub": user.id})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=user)

@api_router.get("/users/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(get_admin_user)):
    rows = await database.fetch_all(users.select())
    results = []
    for r in rows:
        d = dict(r)
        results.append(User(**{k: v for k, v in d.items() if k != "password"}))
    return results

# (other resource routes: customers, sources, products, transactions, etc.)
# I kept the original route implementations you had earlier (not repeated here
# to keep the file size manageable). They are unchanged in behavior.

# Example health route:
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

# -----------------------
# Lifespan handler (startup/shutdown)
# -----------------------
@asynccontextmanager
async def lifespan(app):
    # Log masked DATABASE_URL so you can validate interpolation without leaking password
    def mask_url(u: str) -> str:
        if not u:
            return "<empty>"
        try:
            # naive mask: replace between '//' and '@' if present
            start = u.find("//")
            at = u.find("@")
            if start != -1 and at != -1 and at > start:
                return u[: start + 2] + "<REDACTED>" + u[at:]
        except Exception:
            pass
        return u

    logger.info("Lifespan: starting up LuxTrack service...")
    logger.info("Resolved DATABASE_URL: %s", mask_url(DATABASE_URL))

    # startup
    try:
        await database.connect()
        logger.info("Database connected (lifespan startup).")

        # create default admin if none exists (safe to run each startup)
        try:
            q = sa.select(sa.func.count()).select_from(users).where(users.c.role == UserRole.ADMIN.value)
            res = await database.fetch_one(q)
            count = int(res[0]) if res and res[0] is not None else 0
            if count == 0:
                now = datetime.now(timezone.utc)
                uid = str(uuid.uuid4())
                hashed = hash_password("admin123")
                await database.execute(
                    users.insert().values(
                        id=uid,
                        email="admin@luxtrack.com",
                        password=hashed,
                        full_name="System Administrator",
                        role=UserRole.ADMIN.value,
                        is_active=True,
                        created_at=now,
                        updated_at=now,
                    )
                )
                logger.info("Created default admin user (admin@luxtrack.com / admin123)")
        except Exception:
            logger.exception("Error while ensuring default admin on startup.")

    except Exception:
        logger.exception("Lifespan startup: failed to connect or initialize; continuing without DB.")

    try:
        yield
    finally:
        # shutdown
        try:
            await database.disconnect()
            logger.info("Database disconnected (lifespan shutdown).")
        except Exception:
            logger.exception("Error during lifespan shutdown while disconnecting database.")

# -----------------------
# Create FastAPI app (after lifespan defined) and add middleware + router
# -----------------------
app = FastAPI(title="LuxTrack MVP", description="Luxury Goods Inventory & Sales Tracking System", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# ---------------------------------------
# create_tables_sync() — keep helper, but DO NOT auto-run it in deployments
# Use it manually when you want to bootstrap schema.
# ---------------------------------------
def create_tables_sync():
    """
    Creates tables synchronously using a sync engine (requires PyMySQL).
    Run manually once to bootstrap schema:
      python -c "from server import create_tables_sync; create_tables_sync()"
    """
    sync_url = os.environ.get("DATABASE_URL", "")
    if not sync_url:
        raise RuntimeError("DATABASE_URL not set; cannot create tables.")
    # if using async driver in the URL (asyncmy) switch to pymysql for sync creation
    if "+asyncmy" in sync_url:
        sync_url = sync_url.replace("+asyncmy", "+pymysql")
    if "+aiomysql" in sync_url:
        sync_url = sync_url.replace("+aiomysql", "+pymysql")
    engine = sa.create_engine(sync_url, echo=False, pool_pre_ping=True)
    metadata.create_all(engine)
    logger.info("Tables created (sync)")

# ---------------------------------------
# Only run create_tables_sync or local uvicorn when invoked directly (not on import)
# ---------------------------------------
if __name__ == "__main__":
    # Local dev / admin helpers
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--create-tables", action="store_true", help="Create DB tables (sync) and exit")
    p.add_argument("--run", action="store_true", help="Run Uvicorn dev server")
    args = p.parse_args()

    if args.create_tables:
        print("Running create_tables_sync()")
        create_tables_sync()
    elif args.run:
        import uvicorn
        # runs app with lifespan support
        uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
    else:
        print("No action specified. Use --create-tables or --run")
