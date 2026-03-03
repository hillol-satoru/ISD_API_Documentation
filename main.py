# Daraz Online Shopping Platform API
# Actors: Customer, Seller, Rider, Pickup Point

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from fastapi import FastAPI, Depends, HTTPException, status, APIRouter, Query, Path, Body
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from enum import Enum
from decimal import Decimal
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Daraz API",
    description="API documentation for Daraz Online Shopping Platform - Bangladesh's largest e-commerce marketplace",
    version="1.0.0",
    openapi_tags=[
        {"name": "Auth", "description": "Authentication for all users"},
        {"name": "Customer-Account", "description": "Customer account management"},
        {"name": "Customer-Orders", "description": "Customer order operations"},
        {"name": "Customer-Cart", "description": "Shopping cart operations"},
        {"name": "Customer-Wishlist", "description": "Wishlist management"},
        {"name": "Customer-Reviews", "description": "Product reviews"},
        {"name": "Customer-Returns", "description": "Return and refund requests"},
        {"name": "Products", "description": "Product catalog and search"},
        {"name": "Seller-Dashboard", "description": "Seller center dashboard"},
        {"name": "Seller-Products", "description": "Seller product management"},
        {"name": "Seller-Orders", "description": "Seller order management"},
        {"name": "Seller-Returns", "description": "Seller return handling"},
        {"name": "Seller-Promotions", "description": "Seller promotions and campaigns"},
        {"name": "Seller-Income", "description": "Seller earnings and payouts"},
        {"name": "Rider", "description": "Rider delivery operations"},
        {"name": "PickupPoint", "description": "Pickup point operations"},
        {"name": "Admin", "description": "Admin operations - product verification and dispute handling"}
    ]
)

# Custom OpenAPI schema generator to remove validation error responses
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if "responses" in openapi_schema["paths"][path][method]:
                if "422" in openapi_schema["paths"][path][method]["responses"]:
                    del openapi_schema["paths"][path][method]["responses"]["422"]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================== SECURITY CONFIGURATION ======================

# OAuth2 Bearer Token Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/login")

# JWT Configuration (In production, use environment variables)
SECRET_KEY = "your-super-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# ====================== ENUMS ======================

class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    SELLER = "SELLER"
    RIDER = "RIDER"
    PICKUP_POINT = "PICKUP_POINT"
    ADMIN = "ADMIN"

class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class OrderStatus(str, Enum):
    TO_PAY = "TO_PAY"
    TO_SHIP = "TO_SHIP"
    TO_RECEIVE = "TO_RECEIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class ShipmentStatus(str, Enum):
    ORDERED = "ORDERED"
    PACKED = "PACKED"
    SHIPPED = "SHIPPED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"

class ReturnStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REFUNDED = "REFUNDED"

class ProductStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    REJECTED = "REJECTED"

class PromotionType(str, Enum):
    VOUCHER = "VOUCHER"
    CAMPAIGN = "CAMPAIGN"
    FLASH_SALE = "FLASH_SALE"

class PaymentMethod(str, Enum):
    CASH_ON_DELIVERY = "CASH_ON_DELIVERY"
    BKASH = "BKASH"
    NAGAD = "NAGAD"
    CARD = "CARD"
    DARAZ_WALLET = "DARAZ_WALLET"

class DeliveryStatus(str, Enum):
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"

class PickupStatus(str, Enum):
    PENDING = "PENDING"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    PICKED_UP = "PICKED_UP"
    RETURNED_TO_SELLER = "RETURNED_TO_SELLER"

# ====================== AUTH MODELS ======================

class UserRegister(BaseModel):
    email: EmailStr
    phone: str = Field(..., pattern=r"^01[3-9]\d{8}$")
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = UserRole.CUSTOMER

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_role: UserRole
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenData(BaseModel):
    user_id: str
    role: UserRole
    exp: Optional[datetime] = None

class CurrentUser(BaseModel):
    """Represents the authenticated user from the token."""
    user_id: str
    email: str
    role: UserRole
    full_name: str

class SellerRegister(BaseModel):
    email: EmailStr
    phone: str = Field(..., pattern=r"^01[3-9]\d{8}$")
    password: str = Field(..., min_length=8)
    full_name: str
    store_name: str = Field(..., min_length=3, max_length=100)
    business_type: str
    nid_number: str

# ====================== CUSTOMER MODELS ======================

class CustomerProfile(BaseModel):
    user_id: str
    full_name: str
    email: EmailStr
    phone: str
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    profile_image: Optional[str] = None

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class Address(BaseModel):
    id: str
    full_name: str
    phone: str
    region: str
    city: str
    area: str
    address: str
    landmark: Optional[str] = None
    is_default: bool = False
    label: str = "Home"  # Home, Office, etc.

class AddressCreate(BaseModel):
    full_name: str
    phone: str
    region: str
    city: str
    area: str
    address: str
    landmark: Optional[str] = None
    is_default: bool = False
    label: str = "Home"

# ====================== PRODUCT MODELS ======================

class ProductVariation(BaseModel):
    id: str
    name: str
    options: List[str]

class ProductImage(BaseModel):
    id: str
    url: str
    is_primary: bool = False

class Product(BaseModel):
    id: str
    title: str
    slug: str
    description: str
    category_id: str
    category_name: str
    brand: Optional[str] = None
    price: float
    discount_price: Optional[float] = None
    discount_percentage: Optional[int] = None
    stock: int
    sku: str
    images: List[ProductImage]
    variations: List[ProductVariation] = []
    rating: float = 0.0
    review_count: int = 0
    seller_id: str
    seller_name: str
    status: ProductStatus
    created_at: datetime

class ProductListItem(BaseModel):
    id: str
    title: str
    price: float
    discount_price: Optional[float] = None
    discount_percentage: Optional[int] = None
    image_url: str
    rating: float
    review_count: int
    seller_name: str
    is_free_shipping: bool = False

class Category(BaseModel):
    id: str
    name: str
    slug: str
    icon_url: Optional[str] = None
    parent_id: Optional[str] = None
    children: List["Category"] = []

class SearchFilters(BaseModel):
    category_id: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    brands: Optional[List[str]] = None  # Multiple brands: ["apple", "samsung", "oppo"]
    min_rating: Optional[float] = None
    free_shipping: Optional[bool] = None
    sort_by: str = "relevance"  # relevance, price_low, price_high, newest, rating
    # Dynamic category-based filters
    colors: Optional[List[str]] = None  # ["Black", "White", "Blue"]
    sizes: Optional[List[str]] = None  # ["S", "M", "L", "XL"]
    attributes: Optional[Dict[str, List[str]]] = None  # {"RAM": ["4GB", "8GB"], "Storage": ["64GB", "128GB"]}

class FilterOption(BaseModel):
    """Single filter option with count of matching products."""
    value: str
    count: int
    selected: bool = False

class FilterGroup(BaseModel):
    """Group of filter options (e.g., Brand, Color, RAM)."""
    name: str
    key: str  # API parameter key
    type: str  # checkbox, range, color_picker
    options: List[FilterOption]

class CategoryFilters(BaseModel):
    """Dynamic filters available for a category."""
    category_id: str
    category_name: str
    filters: List[FilterGroup]
    price_range: Dict[str, float]  # {"min": 0, "max": 50000}

class SearchResponse(BaseModel):
    products: List[ProductListItem]
    total_count: int
    page: int
    page_size: int
    filters_applied: Dict[str, Any]
    available_filters: Optional[CategoryFilters] = None  # Dynamic filters for refinement

# ====================== CART MODELS ======================

class CartItem(BaseModel):
    id: str
    product_id: str
    product_title: str
    product_image: str
    variation: Optional[str] = None
    price: float
    quantity: int
    subtotal: float
    seller_id: str
    seller_name: str

class Cart(BaseModel):
    items: List[CartItem]
    item_count: int
    subtotal: float
    shipping_fee: float
    voucher_discount: float = 0.0
    total: float

class CartItemAdd(BaseModel):
    product_id: str
    quantity: int = 1
    variation: Optional[str] = None

class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1)

# ====================== ORDER MODELS ======================

class OrderItem(BaseModel):
    id: str
    product_id: str
    product_title: str
    product_image: str
    variation: Optional[str] = None
    price: float
    quantity: int
    subtotal: float

class Order(BaseModel):
    id: str
    order_number: str
    customer_id: str
    seller_id: str
    seller_name: str
    items: List[OrderItem]
    shipping_address: Address
    payment_method: PaymentMethod
    subtotal: float
    shipping_fee: float
    voucher_discount: float
    total: float
    status: OrderStatus
    shipment_status: ShipmentStatus
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class OrderCreate(BaseModel):
    address_id: str
    payment_method: PaymentMethod
    voucher_code: Optional[str] = None
    delivery_notes: Optional[str] = None

class OrderSummary(BaseModel):
    id: str
    order_number: str
    status: OrderStatus
    total: float
    item_count: int
    thumbnail: str
    created_at: datetime

class TrackingEvent(BaseModel):
    status: ShipmentStatus
    timestamp: datetime
    location: Optional[str] = None
    description: str

class OrderTracking(BaseModel):
    order_id: str
    order_number: str
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    current_status: ShipmentStatus
    estimated_delivery: Optional[date] = None
    timeline: List[TrackingEvent]

# ====================== RETURN MODELS ======================

class ReturnReason(str, Enum):
    DAMAGED = "DAMAGED"
    WRONG_ITEM = "WRONG_ITEM"
    NOT_AS_DESCRIBED = "NOT_AS_DESCRIBED"
    QUALITY_ISSUE = "QUALITY_ISSUE"
    CHANGED_MIND = "CHANGED_MIND"
    OTHER = "OTHER"

class ReturnRequest(BaseModel):
    order_id: str
    order_item_id: str
    reason: ReturnReason
    description: str
    images: List[str] = []
    refund_method: PaymentMethod

class Return(BaseModel):
    id: str
    return_number: str
    order_id: str
    order_number: str
    product_id: str
    product_title: str
    product_image: str
    reason: ReturnReason
    description: str
    images: List[str]
    status: ReturnStatus
    refund_amount: float
    refund_method: PaymentMethod
    created_at: datetime
    updated_at: datetime

# ====================== REVIEW MODELS ======================

class ReviewCreate(BaseModel):
    order_item_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str
    images: List[str] = []

class Review(BaseModel):
    id: str
    product_id: str
    product_title: str
    product_image: str
    customer_id: str
    customer_name: str
    rating: int
    comment: str
    images: List[str]
    seller_reply: Optional[str] = None
    created_at: datetime
    helpful_count: int = 0

class PendingReview(BaseModel):
    order_item_id: str
    product_id: str
    product_title: str
    product_image: str
    order_date: datetime

# ====================== WISHLIST MODELS ======================

class WishlistItem(BaseModel):
    id: str
    product_id: str
    product_title: str
    product_image: str
    price: float
    discount_price: Optional[float] = None
    in_stock: bool
    added_at: datetime

# ====================== HOME PAGE MODELS ======================

class Banner(BaseModel):
    id: str
    image_url: str
    link: str
    title: Optional[str] = None

class FlashSaleProduct(BaseModel):
    id: str
    title: str
    image_url: str
    original_price: float
    sale_price: float
    discount_percentage: int
    sold_count: int
    stock: int

class FlashSale(BaseModel):
    id: str
    title: str
    end_time: datetime
    products: List[FlashSaleProduct]

class HomePageData(BaseModel):
    banners: List[Banner]
    categories: List[Category]
    flash_sale: Optional[FlashSale] = None
    recommended_products: List[ProductListItem]
    sponsored_banners: List[Banner]

# ====================== SELLER MODELS ======================

class SellerDashboard(BaseModel):
    today_sales: float
    today_orders: int
    pending_shipments: int
    pending_returns: int
    total_products: int
    low_stock_products: int
    sales_chart_data: List[Dict[str, Any]]
    recent_orders: List[OrderSummary]

class SellerProfile(BaseModel):
    seller_id: str
    store_name: str
    store_logo: Optional[str] = None
    email: EmailStr
    phone: str
    rating: float
    total_reviews: int
    total_products: int
    joined_date: date
    verified: bool

class ProductCreate(BaseModel):
    title: str = Field(..., min_length=10, max_length=200)
    description: str
    category_id: str
    brand: Optional[str] = None
    price: float = Field(..., gt=0)
    discount_price: Optional[float] = None
    sku: str
    stock: int = Field(..., ge=0)
    images: List[str] = Field(..., min_length=1)
    variations: List[Dict[str, Any]] = []
    weight: Optional[float] = None
    dimensions: Optional[Dict[str, float]] = None

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    discount_price: Optional[float] = None
    stock: Optional[int] = None
    status: Optional[ProductStatus] = None
    images: Optional[List[str]] = None

class SellerOrderUpdate(BaseModel):
    status: OrderStatus
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None

class ReturnDecision(BaseModel):
    approved: bool
    reason: Optional[str] = None

# ====================== PROMOTION MODELS ======================

class VoucherCreate(BaseModel):
    code: str
    discount_type: str  # percentage, fixed
    discount_value: float
    min_purchase: float
    max_discount: Optional[float] = None
    start_date: datetime
    end_date: datetime
    usage_limit: int
    applicable_products: List[str] = []  # empty = all products

class Voucher(BaseModel):
    id: str
    code: str
    discount_type: str
    discount_value: float
    min_purchase: float
    max_discount: Optional[float] = None
    start_date: datetime
    end_date: datetime
    usage_limit: int
    used_count: int
    status: str
    applicable_products: List[str]

class CampaignCreate(BaseModel):
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    discount_percentage: int
    product_ids: List[str]

class Campaign(BaseModel):
    id: str
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    discount_percentage: int
    products_count: int
    status: str
    total_sales: float

# ====================== INCOME MODELS ======================

class IncomeOverview(BaseModel):
    available_balance: float
    pending_balance: float
    total_withdrawn: float
    this_month_earnings: float

class PayoutRecord(BaseModel):
    id: str
    amount: float
    method: str
    account_details: str
    status: str
    requested_at: datetime
    processed_at: Optional[datetime] = None

class WithdrawalRequest(BaseModel):
    amount: float = Field(..., gt=0)
    method: str
    account_details: str

class SellerIncome(BaseModel):
    overview: IncomeOverview
    earnings_chart: List[Dict[str, Any]]
    payout_history: List[PayoutRecord]

# ====================== RIDER MODELS ======================

class DeliveryAssignment(BaseModel):
    id: str
    order_id: str
    order_number: str
    pickup_address: Address
    delivery_address: Address
    customer_name: str
    customer_phone: str
    items_count: int
    payment_method: PaymentMethod
    cod_amount: Optional[float] = None
    status: DeliveryStatus
    assigned_at: datetime
    estimated_delivery: datetime

class DeliveryStatusUpdate(BaseModel):
    status: DeliveryStatus
    notes: Optional[str] = None
    proof_image: Optional[str] = None
    recipient_name: Optional[str] = None

class RiderStats(BaseModel):
    today_deliveries: int
    completed_deliveries: int
    pending_deliveries: int
    total_earnings_today: float
    rating: float

# ====================== PICKUP POINT MODELS ======================

class PickupOrder(BaseModel):
    id: str
    order_id: str
    order_number: str
    customer_name: str
    customer_phone: str
    items_count: int
    status: PickupStatus
    arrived_at: Optional[datetime] = None
    pickup_code: str
    expires_at: datetime

class PickupStatusUpdate(BaseModel):
    status: PickupStatus
    notes: Optional[str] = None

class PickupPointStats(BaseModel):
    pending_pickups: int
    ready_for_pickup: int
    picked_up_today: int
    expired_orders: int

# ====================== MESSAGE RESPONSE ======================

class MessageResponse(BaseModel):
    status: str
    message: str

# ====================== AUTHENTICATION DEPENDENCIES ======================

async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    """
    Dependency to extract and validate the current user from JWT token.
    Returns CurrentUser object with user details.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # In production, decode JWT token here
    # For documentation purposes, we return a mock user
    # Example: payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    # Mock user based on token (in real app, decode from JWT)
    return CurrentUser(
        user_id="usr_123",
        email="user@example.com",
        role=UserRole.CUSTOMER,
        full_name="John Doe"
    )

async def get_current_seller(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Dependency to ensure the current user is a seller."""
    if current_user.role != UserRole.SELLER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Seller account required."
        )
    return current_user

async def get_current_rider(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Dependency to ensure the current user is a rider."""
    if current_user.role != UserRole.RIDER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Rider account required."
        )
    return current_user

async def get_current_pickup_point(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Dependency to ensure the current user is a pickup point operator."""
    if current_user.role != UserRole.PICKUP_POINT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Pickup point account required."
        )
    return current_user

async def get_current_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Dependency to ensure the current user is an admin."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required."
        )
    return current_user

# ====================== ROUTERS ======================

# Auth Router
auth_router = APIRouter(prefix="/v1/auth", tags=["Auth"])

@auth_router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED,
                 responses={201: {"content": {"application/json": {"example": {"status": "success", "message": "Registration successful. Please verify your email."}}}}})
async def register(user_data: UserRegister = Body(..., example={
    "email": "customer@example.com",
    "phone": "01712345678",
    "password": "securePass123",
    "full_name": "John Doe",
    "role": "CUSTOMER"
})):
    """Register a new user (Customer/Seller/Rider)."""
    return {"status": "success", "message": "Registration successful. Please verify your email."}

@auth_router.post("/login", response_model=Token,
                 responses={200: {"content": {"application/json": {"example": {
                     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c3JfMTIzIiwiZW1haWwiOiJjdXN0b21lckBleGFtcGxlLmNvbSIsInJvbGUiOiJDVVNUT01FUiIsImV4cCI6MTcwOTQ1MjgwMH0.abc123",
                     "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c3JfMTIzIiwidHlwZSI6InJlZnJlc2giLCJleHAiOjE3MTAwNTc2MDB9.xyz789",
                     "token_type": "bearer",
                     "user_role": "CUSTOMER",
                     "expires_in": 1800
                 }}}}})
async def login(credentials: UserLogin = Body(..., example={"email": "customer@example.com", "password": "securePass123"})):
    """
    Authenticate user and return access + refresh tokens.
    
    - **access_token**: Short-lived JWT (30 min) for API requests
    - **refresh_token**: Long-lived JWT (7 days) to get new access tokens
    - **expires_in**: Access token lifetime in seconds
    """
    return {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c3JfMTIzIn0.abc",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c3JfMTIzIn0.xyz",
        "token_type": "bearer",
        "user_role": "CUSTOMER",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@auth_router.post("/seller/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED,
                 responses={201: {"content": {"application/json": {"example": {"status": "success", "message": "Seller application submitted. Pending approval."}}}}})
async def register_seller(seller_data: SellerRegister = Body(..., example={
    "email": "seller@example.com",
    "phone": "01812345678",
    "password": "sellerPass123",
    "full_name": "Store Owner",
    "store_name": "Best Electronics BD",
    "business_type": "Electronics",
    "nid_number": "1234567890123"
})):
    """Register as a new seller (Join as Seller page)."""
    return {"status": "success", "message": "Seller application submitted. Pending approval."}

@auth_router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(email: EmailStr = Body(..., embed=True, example="customer@example.com")):
    """Send password reset link."""
    return {"status": "success", "message": "Password reset link sent to your email."}

@auth_router.post("/refresh", response_model=Token,
                 responses={
                     200: {"content": {"application/json": {"example": {
                         "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.newAccessToken.signature",
                         "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.newRefreshToken.signature",
                         "token_type": "bearer",
                         "user_role": "CUSTOMER",
                         "expires_in": 1800
                     }}}},
                     401: {"content": {"application/json": {"example": {"detail": "Invalid or expired refresh token"}}}}
                 })
async def refresh_token(request: RefreshTokenRequest = Body(..., example={
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.currentRefreshToken.signature"
})):
    """
    Get new access token using refresh token.
    
    Use this endpoint when your access token expires. Send your refresh token
    to receive a new access token without requiring the user to login again.
    
    - Refresh tokens are valid for 7 days
    - A new refresh token is also issued (token rotation for security)
    """
    # In production: validate refresh token, check if revoked, issue new tokens
    return {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.newAccessToken.signature",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.newRefreshToken.signature",
        "token_type": "bearer",
        "user_role": "CUSTOMER",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@auth_router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: CurrentUser = Depends(get_current_user),
    refresh_token: str = Body(..., embed=True, example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refreshToken.signature")
):
    """
    Logout user and invalidate refresh token.
    
    This endpoint revokes the refresh token so it cannot be used to get new access tokens.
    Requires valid access token in Authorization header.
    """
    # In production: add refresh token to blacklist/revoked tokens table
    return {"status": "success", "message": "Logged out successfully. Refresh token revoked."}

# Customer Account Router
account_router = APIRouter(prefix="/v1/customer/account", tags=["Customer-Account"])

@account_router.get("/profile", response_model=CustomerProfile,
                   responses={200: {"content": {"application/json": {"example": {
                       "user_id": "usr_123",
                       "full_name": "John Doe",
                       "email": "john@example.com",
                       "phone": "01712345678",
                       "gender": "MALE",
                       "date_of_birth": "1990-05-15",
                       "profile_image": "https://cdn.daraz.com/profiles/usr_123.jpg"
                   }}}}})
async def get_profile():
    """Get customer profile (My Profile page)."""
    return {
        "user_id": "usr_123",
        "full_name": "John Doe",
        "email": "john@example.com",
        "phone": "01712345678",
        "gender": "MALE",
        "date_of_birth": "1990-05-15",
        "profile_image": "https://cdn.daraz.com/profiles/usr_123.jpg"
    }

@account_router.put("/profile", response_model=CustomerProfile)
async def update_profile(
    profile: ProfileUpdate = Body(..., example={
        "full_name": "John Smith",
        "phone": "01712345679",
        "gender": "MALE",
        "date_of_birth": "1990-05-15"
    }),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update customer profile. Requires Bearer token."""
    return {
        "user_id": "usr_123",
        "full_name": "John Smith",
        "email": "john@example.com",
        "phone": "01712345679",
        "gender": "MALE",
        "date_of_birth": "1990-05-15",
        "profile_image": None
    }

@account_router.post("/change-password", response_model=MessageResponse)
async def change_password(
    passwords: PasswordChange = Body(..., example={
        "current_password": "oldPassword123",
        "new_password": "newSecurePass456"
    }),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Change account password. Requires Bearer token."""
    return {"status": "success", "message": "Password changed successfully."}

@account_router.get("/addresses", response_model=List[Address],
                   responses={200: {"content": {"application/json": {"example": [{
                       "id": "addr_1",
                       "full_name": "John Doe",
                       "phone": "01712345678",
                       "region": "Dhaka",
                       "city": "Dhaka",
                       "area": "Gulshan",
                       "address": "House 25, Road 103, Gulshan-2",
                       "landmark": "Near City Bank",
                       "is_default": True,
                       "label": "Home"
                   }]}}}})
async def get_addresses(current_user: CurrentUser = Depends(get_current_user)):
    """Get all saved addresses (Address Book page). Requires Bearer token."""
    return [{
        "id": "addr_1",
        "full_name": "John Doe",
        "phone": "01712345678",
        "region": "Dhaka",
        "city": "Dhaka",
        "area": "Gulshan",
        "address": "House 25, Road 103, Gulshan-2",
        "landmark": "Near City Bank",
        "is_default": True,
        "label": "Home"
    }]

@account_router.post("/addresses", response_model=Address, status_code=status.HTTP_201_CREATED)
async def add_address(
    address: AddressCreate = Body(..., example={
        "full_name": "John Doe",
        "phone": "01712345678",
        "region": "Dhaka",
        "city": "Dhaka",
        "area": "Banani",
        "address": "House 10, Road 12, Banani",
        "landmark": "Near Banani Supermarket",
        "is_default": False,
        "label": "Office"
    }),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Add new address. Requires Bearer token."""
    return {
        "id": "addr_2",
        "full_name": "John Doe",
        "phone": "01712345678",
        "region": "Dhaka",
        "city": "Dhaka",
        "area": "Banani",
        "address": "House 10, Road 12, Banani",
        "landmark": "Near Banani Supermarket",
        "is_default": False,
        "label": "Office"
    }

@account_router.put("/addresses/{address_id}", response_model=Address)
async def update_address(
    address_id: str = Path(..., example="addr_1"),
    address: AddressCreate = Body(...),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update existing address. Requires Bearer token."""
    return {
        "id": address_id,
        "full_name": address.full_name,
        "phone": address.phone,
        "region": address.region,
        "city": address.city,
        "area": address.area,
        "address": address.address,
        "landmark": address.landmark,
        "is_default": address.is_default,
        "label": address.label
    }

@account_router.delete("/addresses/{address_id}", response_model=MessageResponse)
async def delete_address(
    address_id: str = Path(..., example="addr_1"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Delete an address. Requires Bearer token."""
    return {"status": "success", "message": "Address deleted successfully."}

@account_router.put("/addresses/{address_id}/default", response_model=MessageResponse)
async def set_default_address(
    address_id: str = Path(..., example="addr_1"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Set address as default. Requires Bearer token."""
    return {"status": "success", "message": "Default address updated."}

# Customer Orders Router
orders_router = APIRouter(prefix="/v1/customer/orders", tags=["Customer-Orders"])

@orders_router.get("", response_model=List[OrderSummary],
                  responses={200: {"content": {"application/json": {"example": [{
                      "id": "ord_123",
                      "order_number": "DRZ-2024-001234",
                      "status": "TO_RECEIVE",
                      "total": 2500.00,
                      "item_count": 2,
                      "thumbnail": "https://cdn.daraz.com/products/p1.jpg",
                      "created_at": "2024-01-15T10:30:00"
                  }]}}}})
async def get_orders(
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get customer orders (My Orders page with tabs). Requires Bearer token."""
    return [{
        "id": "ord_123",
        "order_number": "DRZ-2024-001234",
        "status": "TO_RECEIVE",
        "total": 2500.00,
        "item_count": 2,
        "thumbnail": "https://cdn.daraz.com/products/p1.jpg",
        "created_at": "2024-01-15T10:30:00"
    }]

@orders_router.get("/{order_id}", response_model=Order,
                  responses={200: {"content": {"application/json": {"example": {
                      "id": "ord_123",
                      "order_number": "DRZ-2024-001234",
                      "customer_id": "usr_123",
                      "seller_id": "sel_456",
                      "seller_name": "Best Electronics BD",
                      "items": [{
                          "id": "item_1",
                          "product_id": "prod_789",
                          "product_title": "Wireless Bluetooth Earbuds",
                          "product_image": "https://cdn.daraz.com/products/p1.jpg",
                          "variation": "Black",
                          "price": 1200.00,
                          "quantity": 1,
                          "subtotal": 1200.00
                      }],
                      "shipping_address": {
                          "id": "addr_1",
                          "full_name": "John Doe",
                          "phone": "01712345678",
                          "region": "Dhaka",
                          "city": "Dhaka",
                          "area": "Gulshan",
                          "address": "House 25, Road 103",
                          "landmark": None,
                          "is_default": True,
                          "label": "Home"
                      },
                      "payment_method": "CASH_ON_DELIVERY",
                      "subtotal": 1200.00,
                      "shipping_fee": 60.00,
                      "voucher_discount": 0,
                      "total": 1260.00,
                      "status": "TO_RECEIVE",
                      "shipment_status": "OUT_FOR_DELIVERY",
                      "tracking_number": "TRK123456789",
                      "carrier": "Daraz Express",
                      "created_at": "2024-01-15T10:30:00",
                      "updated_at": "2024-01-16T14:00:00"
                  }}}}})
async def get_order_details(
    order_id: str = Path(..., example="ord_123"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get order details. Requires Bearer token."""
    return {
        "id": "ord_123",
        "order_number": "DRZ-2024-001234",
        "customer_id": "usr_123",
        "seller_id": "sel_456",
        "seller_name": "Best Electronics BD",
        "items": [{
            "id": "item_1",
            "product_id": "prod_789",
            "product_title": "Wireless Bluetooth Earbuds",
            "product_image": "https://cdn.daraz.com/products/p1.jpg",
            "variation": "Black",
            "price": 1200.00,
            "quantity": 1,
            "subtotal": 1200.00
        }],
        "shipping_address": {
            "id": "addr_1",
            "full_name": "John Doe",
            "phone": "01712345678",
            "region": "Dhaka",
            "city": "Dhaka",
            "area": "Gulshan",
            "address": "House 25, Road 103",
            "landmark": None,
            "is_default": True,
            "label": "Home"
        },
        "payment_method": "CASH_ON_DELIVERY",
        "subtotal": 1200.00,
        "shipping_fee": 60.00,
        "voucher_discount": 0,
        "total": 1260.00,
        "status": "TO_RECEIVE",
        "shipment_status": "OUT_FOR_DELIVERY",
        "tracking_number": "TRK123456789",
        "carrier": "Daraz Express",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

@orders_router.get("/{order_id}/tracking", response_model=OrderTracking,
                  responses={200: {"content": {"application/json": {"example": {
                      "order_id": "ord_123",
                      "order_number": "DRZ-2024-001234",
                      "tracking_number": "TRK123456789",
                      "carrier": "Daraz Express",
                      "current_status": "OUT_FOR_DELIVERY",
                      "estimated_delivery": "2024-01-17",
                      "timeline": [
                          {"status": "ORDERED", "timestamp": "2024-01-15T10:30:00", "location": None, "description": "Order placed successfully"},
                          {"status": "PACKED", "timestamp": "2024-01-15T14:00:00", "location": "Seller Warehouse", "description": "Package ready for pickup"},
                          {"status": "SHIPPED", "timestamp": "2024-01-16T09:00:00", "location": "Dhaka Hub", "description": "Package picked up by courier"},
                          {"status": "OUT_FOR_DELIVERY", "timestamp": "2024-01-17T08:00:00", "location": "Gulshan Area", "description": "Out for delivery"}
                      ]
                  }}}}})
async def track_order(
    order_id: str = Path(..., example="ord_123"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Track order shipment (Order Tracking page). Requires Bearer token."""
    return {
        "order_id": "ord_123",
        "order_number": "DRZ-2024-001234",
        "tracking_number": "TRK123456789",
        "carrier": "Daraz Express",
        "current_status": "OUT_FOR_DELIVERY",
        "estimated_delivery": "2024-01-17",
        "timeline": [
            {"status": "ORDERED", "timestamp": datetime.now(), "location": None, "description": "Order placed successfully"},
            {"status": "PACKED", "timestamp": datetime.now(), "location": "Seller Warehouse", "description": "Package ready for pickup"},
            {"status": "SHIPPED", "timestamp": datetime.now(), "location": "Dhaka Hub", "description": "Package picked up by courier"},
            {"status": "OUT_FOR_DELIVERY", "timestamp": datetime.now(), "location": "Gulshan Area", "description": "Out for delivery"}
        ]
    }

@orders_router.post("/{order_id}/cancel", response_model=MessageResponse)
async def cancel_order(
    order_id: str = Path(..., example="ord_123"),
    reason: str = Body(..., embed=True, example="Changed my mind"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Cancel an order (only if not shipped yet). Requires Bearer token."""
    return {"status": "success", "message": "Order cancelled successfully."}

# Cart Router
cart_router = APIRouter(prefix="/v1/customer/cart", tags=["Customer-Cart"])

@cart_router.get("", response_model=Cart,
                responses={200: {"content": {"application/json": {"example": {
                    "items": [{
                        "id": "cart_item_1",
                        "product_id": "prod_123",
                        "product_title": "Wireless Bluetooth Earbuds",
                        "product_image": "https://cdn.daraz.com/products/p1.jpg",
                        "variation": "Black",
                        "price": 1200.00,
                        "quantity": 2,
                        "subtotal": 2400.00,
                        "seller_id": "sel_456",
                        "seller_name": "Best Electronics BD"
                    }],
                    "item_count": 2,
                    "subtotal": 2400.00,
                    "shipping_fee": 60.00,
                    "voucher_discount": 0,
                    "total": 2460.00
                }}}}})
async def get_cart(current_user: CurrentUser = Depends(get_current_user)):
    """Get shopping cart (Cart page). Requires Bearer token."""
    return {
        "items": [{
            "id": "cart_item_1",
            "product_id": "prod_123",
            "product_title": "Wireless Bluetooth Earbuds",
            "product_image": "https://cdn.daraz.com/products/p1.jpg",
            "variation": "Black",
            "price": 1200.00,
            "quantity": 2,
            "subtotal": 2400.00,
            "seller_id": "sel_456",
            "seller_name": "Best Electronics BD"
        }],
        "item_count": 2,
        "subtotal": 2400.00,
        "shipping_fee": 60.00,
        "voucher_discount": 0,
        "total": 2460.00
    }

@cart_router.post("/items", response_model=Cart, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    item: CartItemAdd = Body(..., example={
        "product_id": "prod_123",
        "quantity": 1,
        "variation": "Black"
    }),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Add item to cart. Requires Bearer token."""
    return {
        "items": [{
            "id": "cart_item_1",
            "product_id": "prod_123",
            "product_title": "Wireless Bluetooth Earbuds",
            "product_image": "https://cdn.daraz.com/products/p1.jpg",
            "variation": "Black",
            "price": 1200.00,
            "quantity": 1,
            "subtotal": 1200.00,
            "seller_id": "sel_456",
            "seller_name": "Best Electronics BD"
        }],
        "item_count": 1,
        "subtotal": 1200.00,
        "shipping_fee": 60.00,
        "voucher_discount": 0,
        "total": 1260.00
    }

@cart_router.put("/items/{item_id}", response_model=Cart)
async def update_cart_item(
    item_id: str = Path(..., example="cart_item_1"),
    update: CartItemUpdate = Body(..., example={"quantity": 3}),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update cart item quantity. Requires Bearer token."""
    return {
        "items": [{
            "id": item_id,
            "product_id": "prod_123",
            "product_title": "Wireless Bluetooth Earbuds",
            "product_image": "https://cdn.daraz.com/products/p1.jpg",
            "variation": "Black",
            "price": 1200.00,
            "quantity": 3,
            "subtotal": 3600.00,
            "seller_id": "sel_456",
            "seller_name": "Best Electronics BD"
        }],
        "item_count": 3,
        "subtotal": 3600.00,
        "shipping_fee": 60.00,
        "voucher_discount": 0,
        "total": 3660.00
    }

@cart_router.delete("/items/{item_id}", response_model=MessageResponse)
async def remove_from_cart(
    item_id: str = Path(..., example="cart_item_1"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Remove item from cart. Requires Bearer token."""
    return {"status": "success", "message": "Item removed from cart."}

@cart_router.post("/apply-voucher", response_model=Cart)
async def apply_voucher(
    voucher_code: str = Body(..., embed=True, example="SAVE100"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Apply voucher code to cart. Requires Bearer token."""
    return {
        "items": [{
            "id": "cart_item_1",
            "product_id": "prod_123",
            "product_title": "Wireless Bluetooth Earbuds",
            "product_image": "https://cdn.daraz.com/products/p1.jpg",
            "variation": "Black",
            "price": 1200.00,
            "quantity": 2,
            "subtotal": 2400.00,
            "seller_id": "sel_456",
            "seller_name": "Best Electronics BD"
        }],
        "item_count": 2,
        "subtotal": 2400.00,
        "shipping_fee": 60.00,
        "voucher_discount": 100.00,
        "total": 2360.00
    }

@cart_router.post("/checkout", response_model=Order, status_code=status.HTTP_201_CREATED)
async def checkout(
    order_data: OrderCreate = Body(..., example={
        "address_id": "addr_1",
        "payment_method": "CASH_ON_DELIVERY",
        "voucher_code": "SAVE100",
        "delivery_notes": "Please call before delivery"
    }),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Place order (Checkout page). Requires Bearer token."""
    return {
        "id": "ord_new_123",
        "order_number": "DRZ-2024-001235",
        "customer_id": "usr_123",
        "seller_id": "sel_456",
        "seller_name": "Best Electronics BD",
        "items": [{
            "id": "item_1",
            "product_id": "prod_123",
            "product_title": "Wireless Bluetooth Earbuds",
            "product_image": "https://cdn.daraz.com/products/p1.jpg",
            "variation": "Black",
            "price": 1200.00,
            "quantity": 2,
            "subtotal": 2400.00
        }],
        "shipping_address": {
            "id": "addr_1",
            "full_name": "John Doe",
            "phone": "01712345678",
            "region": "Dhaka",
            "city": "Dhaka",
            "area": "Gulshan",
            "address": "House 25, Road 103",
            "landmark": None,
            "is_default": True,
            "label": "Home"
        },
        "payment_method": "CASH_ON_DELIVERY",
        "subtotal": 2400.00,
        "shipping_fee": 60.00,
        "voucher_discount": 100.00,
        "total": 2360.00,
        "status": "TO_PAY",
        "shipment_status": "ORDERED",
        "tracking_number": None,
        "carrier": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

# Wishlist Router
wishlist_router = APIRouter(prefix="/v1/customer/wishlist", tags=["Customer-Wishlist"])

@wishlist_router.get("", response_model=List[WishlistItem],
                    responses={200: {"content": {"application/json": {"example": [{
                        "id": "wish_1",
                        "product_id": "prod_456",
                        "product_title": "Samsung Galaxy Watch",
                        "product_image": "https://cdn.daraz.com/products/watch.jpg",
                        "price": 25000.00,
                        "discount_price": 22000.00,
                        "in_stock": True,
                        "added_at": "2024-01-10T15:30:00"
                    }]}}}})
async def get_wishlist(current_user: CurrentUser = Depends(get_current_user)):
    """Get wishlist items (My Wishlist page). Requires Bearer token."""
    return [{
        "id": "wish_1",
        "product_id": "prod_456",
        "product_title": "Samsung Galaxy Watch",
        "product_image": "https://cdn.daraz.com/products/watch.jpg",
        "price": 25000.00,
        "discount_price": 22000.00,
        "in_stock": True,
        "added_at": datetime.now()
    }]

@wishlist_router.post("/{product_id}", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(
    product_id: str = Path(..., example="prod_456"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Add product to wishlist. Requires Bearer token."""
    return {"status": "success", "message": "Added to wishlist."}

@wishlist_router.delete("/{product_id}", response_model=MessageResponse)
async def remove_from_wishlist(
    product_id: str = Path(..., example="prod_456"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Remove product from wishlist. Requires Bearer token."""
    return {"status": "success", "message": "Removed from wishlist."}

@wishlist_router.post("/{product_id}/move-to-cart", response_model=MessageResponse)
async def move_to_cart(
    product_id: str = Path(..., example="prod_456"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Move wishlist item to cart. Requires Bearer token."""
    return {"status": "success", "message": "Item moved to cart."}

# Reviews Router
reviews_router = APIRouter(prefix="/v1/customer/reviews", tags=["Customer-Reviews"])

@reviews_router.get("/pending", response_model=List[PendingReview],
                   responses={200: {"content": {"application/json": {"example": [{
                       "order_item_id": "item_123",
                       "product_id": "prod_789",
                       "product_title": "Wireless Earbuds",
                       "product_image": "https://cdn.daraz.com/products/p1.jpg",
                       "order_date": "2024-01-10T10:00:00"
                   }]}}}})
async def get_pending_reviews(current_user: CurrentUser = Depends(get_current_user)):
    """Get products pending review (To Review tab). Requires Bearer token."""
    return [{
        "order_item_id": "item_123",
        "product_id": "prod_789",
        "product_title": "Wireless Earbuds",
        "product_image": "https://cdn.daraz.com/products/p1.jpg",
        "order_date": datetime.now()
    }]

@reviews_router.get("/submitted", response_model=List[Review],
                   responses={200: {"content": {"application/json": {"example": [{
                       "id": "rev_123",
                       "product_id": "prod_456",
                       "product_title": "Samsung Galaxy Watch",
                       "product_image": "https://cdn.daraz.com/products/watch.jpg",
                       "customer_id": "usr_123",
                       "customer_name": "John D.",
                       "rating": 5,
                       "comment": "Excellent product! Fast delivery.",
                       "images": ["https://cdn.daraz.com/reviews/r1.jpg"],
                       "seller_reply": "Thank you for your feedback!",
                       "created_at": "2024-01-12T14:00:00",
                       "helpful_count": 5
                   }]}}}})
async def get_submitted_reviews(current_user: CurrentUser = Depends(get_current_user)):
    """Get submitted reviews (Reviewed tab). Requires Bearer token."""
    return [{
        "id": "rev_123",
        "product_id": "prod_456",
        "product_title": "Samsung Galaxy Watch",
        "product_image": "https://cdn.daraz.com/products/watch.jpg",
        "customer_id": "usr_123",
        "customer_name": "John D.",
        "rating": 5,
        "comment": "Excellent product! Fast delivery.",
        "images": ["https://cdn.daraz.com/reviews/r1.jpg"],
        "seller_reply": "Thank you for your feedback!",
        "created_at": datetime.now(),
        "helpful_count": 5
    }]

@reviews_router.post("", response_model=Review, status_code=status.HTTP_201_CREATED)
async def submit_review(
    review: ReviewCreate = Body(..., example={
        "order_item_id": "item_123",
        "rating": 5,
        "comment": "Great product, highly recommend!",
        "images": ["https://cdn.daraz.com/reviews/user_upload.jpg"]
    }),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Submit a product review. Requires Bearer token."""
    return {
        "id": "rev_new",
        "product_id": "prod_789",
        "product_title": "Wireless Earbuds",
        "product_image": "https://cdn.daraz.com/products/p1.jpg",
        "customer_id": "usr_123",
        "customer_name": "John D.",
        "rating": 5,
        "comment": "Great product, highly recommend!",
        "images": ["https://cdn.daraz.com/reviews/user_upload.jpg"],
        "seller_reply": None,
        "created_at": datetime.now(),
        "helpful_count": 0
    }

# Returns Router
returns_router = APIRouter(prefix="/v1/customer/returns", tags=["Customer-Returns"])

@returns_router.get("", response_model=List[Return],
                   responses={200: {"content": {"application/json": {"example": [{
                       "id": "ret_123",
                       "return_number": "RET-2024-0001",
                       "order_id": "ord_123",
                       "order_number": "DRZ-2024-001234",
                       "product_id": "prod_789",
                       "product_title": "Wireless Earbuds",
                       "product_image": "https://cdn.daraz.com/products/p1.jpg",
                       "reason": "DAMAGED",
                       "description": "Product arrived with broken case",
                       "images": ["https://cdn.daraz.com/returns/damage1.jpg"],
                       "status": "APPROVED",
                       "refund_amount": 1200.00,
                       "refund_method": "BKASH",
                       "created_at": "2024-01-15T10:00:00",
                       "updated_at": "2024-01-16T14:00:00"
                   }]}}}})
async def get_returns(
    status: Optional[ReturnStatus] = Query(None),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get return requests (My Returns page). Requires Bearer token."""
    return [{
        "id": "ret_123",
        "return_number": "RET-2024-0001",
        "order_id": "ord_123",
        "order_number": "DRZ-2024-001234",
        "product_id": "prod_789",
        "product_title": "Wireless Earbuds",
        "product_image": "https://cdn.daraz.com/products/p1.jpg",
        "reason": "DAMAGED",
        "description": "Product arrived with broken case",
        "images": ["https://cdn.daraz.com/returns/damage1.jpg"],
        "status": "APPROVED",
        "refund_amount": 1200.00,
        "refund_method": "BKASH",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }]

@returns_router.get("/{return_id}", response_model=Return)
async def get_return_details(
    return_id: str = Path(..., example="ret_123"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get return request details (Return Details page). Requires Bearer token."""
    return {
        "id": "ret_123",
        "return_number": "RET-2024-0001",
        "order_id": "ord_123",
        "order_number": "DRZ-2024-001234",
        "product_id": "prod_789",
        "product_title": "Wireless Earbuds",
        "product_image": "https://cdn.daraz.com/products/p1.jpg",
        "reason": "DAMAGED",
        "description": "Product arrived with broken case",
        "images": ["https://cdn.daraz.com/returns/damage1.jpg"],
        "status": "APPROVED",
        "refund_amount": 1200.00,
        "refund_method": "BKASH",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

@returns_router.post("", response_model=Return, status_code=status.HTTP_201_CREATED)
async def create_return(
    return_request: ReturnRequest = Body(..., example={
        "order_id": "ord_123",
        "order_item_id": "item_1",
        "reason": "DAMAGED",
        "description": "Product arrived with broken case",
        "images": ["https://cdn.daraz.com/returns/damage1.jpg"],
        "refund_method": "BKASH"
    }),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Create a return request. Requires Bearer token."""
    return {
        "id": "ret_new",
        "return_number": "RET-2024-0002",
        "order_id": "ord_123",
        "order_number": "DRZ-2024-001234",
        "product_id": "prod_789",
        "product_title": "Wireless Earbuds",
        "product_image": "https://cdn.daraz.com/products/p1.jpg",
        "reason": "DAMAGED",
        "description": "Product arrived with broken case",
        "images": ["https://cdn.daraz.com/returns/damage1.jpg"],
        "status": "REQUESTED",
        "refund_amount": 1200.00,
        "refund_method": "BKASH",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

# Products Router (Public)
products_router = APIRouter(prefix="/v1/products", tags=["Products"])

@products_router.get("/home", response_model=HomePageData,
                    responses={200: {"content": {"application/json": {"example": {
                        "banners": [{"id": "b1", "image_url": "https://cdn.daraz.com/banners/sale.jpg", "link": "/campaign/11-11", "title": "11.11 Sale"}],
                        "categories": [{"id": "cat1", "name": "Electronics", "slug": "electronics", "icon_url": "https://cdn.daraz.com/icons/electronics.png", "parent_id": None, "children": []}],
                        "flash_sale": {
                            "id": "fs1",
                            "title": "Flash Sale",
                            "end_time": "2024-01-20T23:59:59",
                            "products": [{"id": "p1", "title": "Earbuds", "image_url": "https://cdn.daraz.com/p1.jpg", "original_price": 1500, "sale_price": 999, "discount_percentage": 33, "sold_count": 150, "stock": 50}]
                        },
                        "recommended_products": [{"id": "p2", "title": "Smart Watch", "price": 5000, "discount_price": 4500, "discount_percentage": 10, "image_url": "https://cdn.daraz.com/p2.jpg", "rating": 4.5, "review_count": 120, "seller_name": "Tech Store", "is_free_shipping": True}],
                        "sponsored_banners": [{"id": "sb1", "image_url": "https://cdn.daraz.com/sponsored/brand.jpg", "link": "/brand/samsung", "title": None}]
                    }}}}})
async def get_home_page():
    """Get home page data (banners, categories, flash sale, recommendations)."""
    return {
        "banners": [{"id": "b1", "image_url": "https://cdn.daraz.com/banners/sale.jpg", "link": "/campaign/11-11", "title": "11.11 Sale"}],
        "categories": [{"id": "cat1", "name": "Electronics", "slug": "electronics", "icon_url": "https://cdn.daraz.com/icons/electronics.png", "parent_id": None, "children": []}],
        "flash_sale": {
            "id": "fs1",
            "title": "Flash Sale",
            "end_time": datetime.now() + timedelta(hours=12),
            "products": [{"id": "p1", "title": "Earbuds", "image_url": "https://cdn.daraz.com/p1.jpg", "original_price": 1500, "sale_price": 999, "discount_percentage": 33, "sold_count": 150, "stock": 50}]
        },
        "recommended_products": [{"id": "p2", "title": "Smart Watch", "price": 5000, "discount_price": 4500, "discount_percentage": 10, "image_url": "https://cdn.daraz.com/p2.jpg", "rating": 4.5, "review_count": 120, "seller_name": "Tech Store", "is_free_shipping": True}],
        "sponsored_banners": [{"id": "sb1", "image_url": "https://cdn.daraz.com/sponsored/brand.jpg", "link": "/brand/samsung", "title": None}]
    }

@products_router.get("/search", response_model=SearchResponse,
                    responses={200: {"content": {"application/json": {"example": {
                        "products": [{"id": "p1", "title": "Wireless Bluetooth Earbuds", "price": 1500, "discount_price": 1200, "discount_percentage": 20, "image_url": "https://cdn.daraz.com/p1.jpg", "rating": 4.3, "review_count": 250, "seller_name": "Audio Store", "is_free_shipping": False}],
                        "total_count": 156,
                        "page": 1,
                        "page_size": 20,
                        "filters_applied": {
                            "query": "earbuds",
                            "category": "electronics",
                            "brands": ["samsung", "apple"],
                            "colors": ["black"],
                            "attributes": {"RAM": ["8GB"]}
                        },
                        "available_filters": {
                            "category_id": "cat_electronics",
                            "category_name": "Electronics",
                            "filters": [
                                {"name": "Brand", "key": "brands", "type": "checkbox", "options": [{"value": "Samsung", "count": 45, "selected": True}, {"value": "Apple", "count": 38, "selected": True}]},
                                {"name": "Color", "key": "colors", "type": "color_picker", "options": [{"value": "Black", "count": 120, "selected": True}]}
                            ],
                            "price_range": {"min": 500, "max": 50000}
                        }
                    }}}}})
async def search_products(
    q: str = Query(..., description="Search query", example="wireless earbuds"),
    category_id: Optional[str] = Query(None, example="cat_electronics"),
    min_price: Optional[float] = Query(None, example=500),
    max_price: Optional[float] = Query(None, example=5000),
    brands: Optional[str] = Query(None, description="Multiple brands separated by + (e.g., apple+samsung+oppo)", example="apple+samsung+oppo"),
    colors: Optional[str] = Query(None, description="Multiple colors separated by + (e.g., black+white+blue)", example="black+white"),
    ram: Optional[str] = Query(None, description="RAM options separated by + (e.g., 4GB+8GB)", example="4GB+8GB"),
    storage: Optional[str] = Query(None, description="Storage options separated by + (e.g., 64GB+128GB+256GB)", example="128GB+256GB"),
    screen_size: Optional[str] = Query(None, description="Screen sizes separated by + (e.g., 6.1+6.5+6.7)", example="6.5+6.7"),
    min_rating: Optional[float] = Query(None, ge=1, le=5, example=4.0),
    free_shipping: Optional[bool] = Query(None),
    sort_by: str = Query("relevance", example="price_low"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50)
):
    """
    Search products with filters.
    
    **Multiple Value Filtering:**
    Use + to separate multiple values for the same filter:
    - `brands=apple+samsung+oppo` → Products from Apple OR Samsung OR Oppo
    - `colors=black+white` → Products in Black OR White
    - `ram=4GB+8GB` → Products with 4GB OR 8GB RAM
    - `storage=128GB+256GB` → Products with 128GB OR 256GB storage
    
    **Dynamic Filters:**
    The response includes `available_filters` showing all filterable attributes
    for the current category with product counts.
    """
    # Parse multiple values
    parsed_brands = brands.split("+") if brands else None
    parsed_colors = colors.split("+") if colors else None
    parsed_attributes = {}
    if ram:
        parsed_attributes["RAM"] = ram.split("+")
    if storage:
        parsed_attributes["Storage"] = storage.split("+")
    if screen_size:
        parsed_attributes["Screen Size"] = screen_size.split("+")
    
    return {
        "products": [{"id": "p1", "title": "Wireless Bluetooth Earbuds", "price": 1500, "discount_price": 1200, "discount_percentage": 20, "image_url": "https://cdn.daraz.com/p1.jpg", "rating": 4.3, "review_count": 250, "seller_name": "Audio Store", "is_free_shipping": False}],
        "total_count": 156,
        "page": page,
        "page_size": page_size,
        "filters_applied": {
            "query": q,
            "category": category_id,
            "brands": parsed_brands,
            "colors": parsed_colors,
            "attributes": parsed_attributes if parsed_attributes else None
        },
        "available_filters": {
            "category_id": category_id or "cat_electronics",
            "category_name": "Electronics",
            "filters": [
                {"name": "Brand", "key": "brands", "type": "checkbox", "options": [
                    {"value": "Samsung", "count": 245, "selected": parsed_brands and "samsung" in [b.lower() for b in parsed_brands]},
                    {"value": "Apple", "count": 189, "selected": parsed_brands and "apple" in [b.lower() for b in parsed_brands]},
                    {"value": "Oppo", "count": 156, "selected": parsed_brands and "oppo" in [b.lower() for b in parsed_brands]},
                    {"value": "Xiaomi", "count": 134, "selected": False},
                    {"value": "Realme", "count": 98, "selected": False}
                ]},
                {"name": "Color", "key": "colors", "type": "color_picker", "options": [
                    {"value": "Black", "count": 320, "selected": parsed_colors and "black" in [c.lower() for c in parsed_colors]},
                    {"value": "White", "count": 245, "selected": parsed_colors and "white" in [c.lower() for c in parsed_colors]},
                    {"value": "Blue", "count": 178, "selected": False},
                    {"value": "Red", "count": 89, "selected": False}
                ]},
                {"name": "RAM", "key": "ram", "type": "checkbox", "options": [
                    {"value": "4GB", "count": 156, "selected": "RAM" in parsed_attributes and "4GB" in parsed_attributes["RAM"]},
                    {"value": "6GB", "count": 198, "selected": "RAM" in parsed_attributes and "6GB" in parsed_attributes["RAM"]},
                    {"value": "8GB", "count": 245, "selected": "RAM" in parsed_attributes and "8GB" in parsed_attributes["RAM"]},
                    {"value": "12GB", "count": 89, "selected": "RAM" in parsed_attributes and "12GB" in parsed_attributes["RAM"]}
                ]},
                {"name": "Storage", "key": "storage", "type": "checkbox", "options": [
                    {"value": "64GB", "count": 134, "selected": "Storage" in parsed_attributes and "64GB" in parsed_attributes["Storage"]},
                    {"value": "128GB", "count": 267, "selected": "Storage" in parsed_attributes and "128GB" in parsed_attributes["Storage"]},
                    {"value": "256GB", "count": 189, "selected": "Storage" in parsed_attributes and "256GB" in parsed_attributes["Storage"]},
                    {"value": "512GB", "count": 67, "selected": "Storage" in parsed_attributes and "512GB" in parsed_attributes["Storage"]}
                ]}
            ],
            "price_range": {"min": 5000, "max": 150000}
        }
    }

@products_router.get("/categories", response_model=List[Category])
async def get_categories():
    """Get all product categories."""
    return [{
        "id": "cat1",
        "name": "Electronics",
        "slug": "electronics",
        "icon_url": "https://cdn.daraz.com/icons/electronics.png",
        "parent_id": None,
        "children": [
            {"id": "cat1_1", "name": "Mobile Phones", "slug": "mobile-phones", "icon_url": None, "parent_id": "cat1", "children": []},
            {"id": "cat1_2", "name": "Laptops", "slug": "laptops", "icon_url": None, "parent_id": "cat1", "children": []}
        ]
    }]

@products_router.get("/categories/{category_id}/filters", response_model=CategoryFilters,
                    responses={200: {"content": {"application/json": {"example": {
                        "category_id": "cat_mobile_phones",
                        "category_name": "Mobile Phones",
                        "filters": [
                            {"name": "Brand", "key": "brands", "type": "checkbox", "options": [
                                {"value": "Samsung", "count": 245, "selected": False},
                                {"value": "Apple", "count": 189, "selected": False},
                                {"value": "Oppo", "count": 156, "selected": False}
                            ]},
                            {"name": "RAM", "key": "ram", "type": "checkbox", "options": [
                                {"value": "4GB", "count": 156, "selected": False},
                                {"value": "8GB", "count": 245, "selected": False}
                            ]},
                            {"name": "Storage", "key": "storage", "type": "checkbox", "options": [
                                {"value": "64GB", "count": 134, "selected": False},
                                {"value": "128GB", "count": 267, "selected": False}
                            ]},
                            {"name": "Color", "key": "colors", "type": "color_picker", "options": [
                                {"value": "Black", "count": 320, "selected": False},
                                {"value": "White", "count": 245, "selected": False}
                            ]}
                        ],
                        "price_range": {"min": 8000, "max": 180000}
                    }}}}})
async def get_category_filters(category_id: str = Path(..., example="cat_mobile_phones")):
    """
    Get available filters for a specific category.
    
    This endpoint returns dynamic filters based on the category:
    - **Mobile Phones**: Brand, RAM, Storage, Color, Screen Size
    - **Laptops**: Brand, RAM, Storage, Processor, Screen Size
    - **Clothing**: Brand, Size, Color, Material
    - **Shoes**: Brand, Size, Color, Type
    
    Each filter option includes the count of matching products.
    """
    # Dynamic filters based on category
    if "mobile" in category_id.lower() or "phone" in category_id.lower():
        filters = [
            {"name": "Brand", "key": "brands", "type": "checkbox", "options": [
                {"value": "Samsung", "count": 245, "selected": False},
                {"value": "Apple", "count": 189, "selected": False},
                {"value": "Oppo", "count": 156, "selected": False},
                {"value": "Xiaomi", "count": 134, "selected": False},
                {"value": "Realme", "count": 98, "selected": False},
                {"value": "Vivo", "count": 87, "selected": False}
            ]},
            {"name": "RAM", "key": "ram", "type": "checkbox", "options": [
                {"value": "4GB", "count": 156, "selected": False},
                {"value": "6GB", "count": 198, "selected": False},
                {"value": "8GB", "count": 245, "selected": False},
                {"value": "12GB", "count": 89, "selected": False}
            ]},
            {"name": "Storage", "key": "storage", "type": "checkbox", "options": [
                {"value": "64GB", "count": 134, "selected": False},
                {"value": "128GB", "count": 267, "selected": False},
                {"value": "256GB", "count": 189, "selected": False},
                {"value": "512GB", "count": 67, "selected": False}
            ]},
            {"name": "Color", "key": "colors", "type": "color_picker", "options": [
                {"value": "Black", "count": 320, "selected": False},
                {"value": "White", "count": 245, "selected": False},
                {"value": "Blue", "count": 178, "selected": False},
                {"value": "Gold", "count": 134, "selected": False},
                {"value": "Purple", "count": 89, "selected": False}
            ]},
            {"name": "Screen Size", "key": "screen_size", "type": "checkbox", "options": [
                {"value": "6.1 inch", "count": 145, "selected": False},
                {"value": "6.5 inch", "count": 234, "selected": False},
                {"value": "6.7 inch", "count": 189, "selected": False}
            ]}
        ]
        price_range = {"min": 8000, "max": 180000}
        category_name = "Mobile Phones"
    elif "laptop" in category_id.lower():
        filters = [
            {"name": "Brand", "key": "brands", "type": "checkbox", "options": [
                {"value": "HP", "count": 156, "selected": False},
                {"value": "Dell", "count": 134, "selected": False},
                {"value": "Lenovo", "count": 189, "selected": False},
                {"value": "Asus", "count": 145, "selected": False},
                {"value": "Apple", "count": 78, "selected": False}
            ]},
            {"name": "RAM", "key": "ram", "type": "checkbox", "options": [
                {"value": "8GB", "count": 234, "selected": False},
                {"value": "16GB", "count": 189, "selected": False},
                {"value": "32GB", "count": 67, "selected": False}
            ]},
            {"name": "Storage", "key": "storage", "type": "checkbox", "options": [
                {"value": "256GB SSD", "count": 145, "selected": False},
                {"value": "512GB SSD", "count": 234, "selected": False},
                {"value": "1TB SSD", "count": 89, "selected": False}
            ]},
            {"name": "Processor", "key": "processor", "type": "checkbox", "options": [
                {"value": "Intel Core i5", "count": 234, "selected": False},
                {"value": "Intel Core i7", "count": 156, "selected": False},
                {"value": "AMD Ryzen 5", "count": 145, "selected": False},
                {"value": "AMD Ryzen 7", "count": 89, "selected": False},
                {"value": "Apple M2", "count": 45, "selected": False}
            ]}
        ]
        price_range = {"min": 35000, "max": 350000}
        category_name = "Laptops"
    else:
        # Default filters for other categories
        filters = [
            {"name": "Brand", "key": "brands", "type": "checkbox", "options": [
                {"value": "Brand A", "count": 100, "selected": False},
                {"value": "Brand B", "count": 80, "selected": False}
            ]},
            {"name": "Color", "key": "colors", "type": "color_picker", "options": [
                {"value": "Black", "count": 150, "selected": False},
                {"value": "White", "count": 120, "selected": False}
            ]}
        ]
        price_range = {"min": 100, "max": 50000}
        category_name = "Products"
    
    return {
        "category_id": category_id,
        "category_name": category_name,
        "filters": filters,
        "price_range": price_range
    }

@products_router.get("/{product_id}", response_model=Product,
                    responses={200: {"content": {"application/json": {"example": {
                        "id": "prod_123",
                        "title": "Wireless Bluetooth Earbuds TWS Pro",
                        "slug": "wireless-bluetooth-earbuds-tws-pro",
                        "description": "High quality wireless earbuds with noise cancellation...",
                        "category_id": "cat_audio",
                        "category_name": "Audio",
                        "brand": "SoundMax",
                        "price": 1500.00,
                        "discount_price": 1200.00,
                        "discount_percentage": 20,
                        "stock": 45,
                        "sku": "SM-TWS-PRO-001",
                        "images": [{"id": "img1", "url": "https://cdn.daraz.com/products/p1_main.jpg", "is_primary": True}],
                        "variations": [{"id": "var1", "name": "Color", "options": ["Black", "White", "Blue"]}],
                        "rating": 4.5,
                        "review_count": 328,
                        "seller_id": "sel_456",
                        "seller_name": "Audio World BD",
                        "status": "ACTIVE",
                        "created_at": "2023-06-15T10:00:00"
                    }}}}})
async def get_product(product_id: str = Path(..., example="prod_123")):
    """Get product details (Product Page)."""
    return {
        "id": "prod_123",
        "title": "Wireless Bluetooth Earbuds TWS Pro",
        "slug": "wireless-bluetooth-earbuds-tws-pro",
        "description": "High quality wireless earbuds with noise cancellation...",
        "category_id": "cat_audio",
        "category_name": "Audio",
        "brand": "SoundMax",
        "price": 1500.00,
        "discount_price": 1200.00,
        "discount_percentage": 20,
        "stock": 45,
        "sku": "SM-TWS-PRO-001",
        "images": [{"id": "img1", "url": "https://cdn.daraz.com/products/p1_main.jpg", "is_primary": True}],
        "variations": [{"id": "var1", "name": "Color", "options": ["Black", "White", "Blue"]}],
        "rating": 4.5,
        "review_count": 328,
        "seller_id": "sel_456",
        "seller_name": "Audio World BD",
        "status": "ACTIVE",
        "created_at": datetime.now()
    }

@products_router.get("/{product_id}/reviews", response_model=List[Review])
async def get_product_reviews(
    product_id: str = Path(..., example="prod_123"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50)
):
    """Get product reviews."""
    return [{
        "id": "rev_456",
        "product_id": product_id,
        "product_title": "Wireless Bluetooth Earbuds",
        "product_image": "https://cdn.daraz.com/products/p1.jpg",
        "customer_id": "usr_789",
        "customer_name": "Ahmed K.",
        "rating": 5,
        "comment": "Amazing sound quality! Battery life is excellent.",
        "images": [],
        "seller_reply": "Thank you for choosing us!",
        "created_at": datetime.now(),
        "helpful_count": 12
    }]

# ====================== SELLER ROUTERS ======================

seller_dashboard_router = APIRouter(prefix="/v1/seller/dashboard", tags=["Seller-Dashboard"])

@seller_dashboard_router.get("", response_model=SellerDashboard,
                            responses={200: {"content": {"application/json": {"example": {
                                "today_sales": 25600.00,
                                "today_orders": 18,
                                "pending_shipments": 12,
                                "pending_returns": 3,
                                "total_products": 156,
                                "low_stock_products": 8,
                                "sales_chart_data": [{"date": "2024-01-10", "sales": 18500}, {"date": "2024-01-11", "sales": 22000}],
                                "recent_orders": [{"id": "ord_123", "order_number": "DRZ-2024-001234", "status": "TO_SHIP", "total": 2500, "item_count": 2, "thumbnail": "https://cdn.daraz.com/p1.jpg", "created_at": "2024-01-15T10:30:00"}]
                            }}}}})
async def get_seller_dashboard(current_user: CurrentUser = Depends(get_current_seller)):
    """Get seller dashboard data (Seller Center main page). Requires Seller Bearer token."""
    return {
        "today_sales": 25600.00,
        "today_orders": 18,
        "pending_shipments": 12,
        "pending_returns": 3,
        "total_products": 156,
        "low_stock_products": 8,
        "sales_chart_data": [{"date": "2024-01-10", "sales": 18500}, {"date": "2024-01-11", "sales": 22000}],
        "recent_orders": [{"id": "ord_123", "order_number": "DRZ-2024-001234", "status": "TO_SHIP", "total": 2500, "item_count": 2, "thumbnail": "https://cdn.daraz.com/p1.jpg", "created_at": datetime.now()}]
    }

@seller_dashboard_router.get("/profile", response_model=SellerProfile)
async def get_seller_profile():
    """Get seller profile."""
    return {
        "seller_id": "sel_456",
        "store_name": "Best Electronics BD",
        "store_logo": "https://cdn.daraz.com/stores/logo456.jpg",
        "email": "seller@bestelectronics.com",
        "phone": "01812345678",
        "rating": 4.7,
        "total_reviews": 1250,
        "total_products": 156,
        "joined_date": "2022-03-15",
        "verified": True
    }

# Seller Products Router
seller_products_router = APIRouter(prefix="/v1/seller/products", tags=["Seller-Products"])

@seller_products_router.get("", response_model=List[Product],
                           responses={200: {"content": {"application/json": {"example": [{
                               "id": "prod_123",
                               "title": "Wireless Earbuds",
                               "slug": "wireless-earbuds",
                               "description": "High quality earbuds",
                               "category_id": "cat_audio",
                               "category_name": "Audio",
                               "brand": "SoundMax",
                               "price": 1500.00,
                               "discount_price": 1200.00,
                               "discount_percentage": 20,
                               "stock": 45,
                               "sku": "SM-001",
                               "images": [{"id": "img1", "url": "https://cdn.daraz.com/p1.jpg", "is_primary": True}],
                               "variations": [],
                               "rating": 4.5,
                               "review_count": 120,
                               "seller_id": "sel_456",
                               "seller_name": "Best Electronics BD",
                               "status": "ACTIVE",
                               "created_at": "2024-01-01T10:00:00"
                           }]}}}})
async def get_seller_products(
    status: Optional[ProductStatus] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_seller)
):
    """Get seller's products (Manage Products page). Requires Seller Bearer token."""
    return [{
        "id": "prod_123",
        "title": "Wireless Earbuds",
        "slug": "wireless-earbuds",
        "description": "High quality earbuds",
        "category_id": "cat_audio",
        "category_name": "Audio",
        "brand": "SoundMax",
        "price": 1500.00,
        "discount_price": 1200.00,
        "discount_percentage": 20,
        "stock": 45,
        "sku": "SM-001",
        "images": [{"id": "img1", "url": "https://cdn.daraz.com/p1.jpg", "is_primary": True}],
        "variations": [],
        "rating": 4.5,
        "review_count": 120,
        "seller_id": "sel_456",
        "seller_name": "Best Electronics BD",
        "status": "ACTIVE",
        "created_at": datetime.now()
    }]

@seller_products_router.post("", response_model=Product, status_code=status.HTTP_201_CREATED)
async def add_product(
    product: ProductCreate = Body(..., example={
        "title": "New Wireless Headphones Premium",
        "description": "Premium noise-cancelling wireless headphones with 40hr battery",
        "category_id": "cat_audio",
        "brand": "AudioMax",
        "price": 8500.00,
        "discount_price": 7500.00,
        "sku": "AM-WH-001",
        "stock": 50,
        "images": ["https://cdn.daraz.com/uploads/headphones1.jpg", "https://cdn.daraz.com/uploads/headphones2.jpg"],
        "variations": [{"name": "Color", "options": ["Black", "Silver"]}],
        "weight": 0.3,
        "dimensions": {"length": 20, "width": 18, "height": 8}
    }),
    current_user: CurrentUser = Depends(get_current_seller)
):
    """Add new product (Add Product page). Requires Seller Bearer token."""
    return {
        "id": "prod_new",
        "title": "New Wireless Headphones Premium",
        "slug": "new-wireless-headphones-premium",
        "description": "Premium noise-cancelling wireless headphones with 40hr battery",
        "category_id": "cat_audio",
        "category_name": "Audio",
        "brand": "AudioMax",
        "price": 8500.00,
        "discount_price": 7500.00,
        "discount_percentage": 12,
        "stock": 50,
        "sku": "AM-WH-001",
        "images": [{"id": "img1", "url": "https://cdn.daraz.com/uploads/headphones1.jpg", "is_primary": True}],
        "variations": [{"id": "var1", "name": "Color", "options": ["Black", "Silver"]}],
        "rating": 0.0,
        "review_count": 0,
        "seller_id": "sel_456",
        "seller_name": "Best Electronics BD",
        "status": "PENDING_APPROVAL",
        "created_at": datetime.now()
    }

@seller_products_router.put("/{product_id}", response_model=Product)
async def update_product(
    product_id: str = Path(..., example="prod_123"),
    product: ProductUpdate = Body(..., example={
        "price": 1400.00,
        "discount_price": 1100.00,
        "stock": 100
    }),
    current_user: CurrentUser = Depends(get_current_seller)
):
    """Update product details (Edit product - extends Set Price). Requires Seller Bearer token."""
    return {
        "id": product_id,
        "title": "Wireless Earbuds",
        "slug": "wireless-earbuds",
        "description": "High quality earbuds",
        "category_id": "cat_audio",
        "category_name": "Audio",
        "brand": "SoundMax",
        "price": 1400.00,
        "discount_price": 1100.00,
        "discount_percentage": 21,
        "stock": 100,
        "sku": "SM-001",
        "images": [{"id": "img1", "url": "https://cdn.daraz.com/p1.jpg", "is_primary": True}],
        "variations": [],
        "rating": 4.5,
        "review_count": 120,
        "seller_id": "sel_456",
        "seller_name": "Best Electronics BD",
        "status": "ACTIVE",
        "created_at": datetime.now()
    }

@seller_products_router.delete("/{product_id}", response_model=MessageResponse)
async def delete_product(
    product_id: str = Path(..., example="prod_123"),
    current_user: CurrentUser = Depends(get_current_seller)
):
    """Delete a product. Requires Seller Bearer token."""
    return {"status": "success", "message": "Product deleted successfully."}

# Seller Orders Router
seller_orders_router = APIRouter(prefix="/v1/seller/orders", tags=["Seller-Orders"])

@seller_orders_router.get("", response_model=List[Order],
                         responses={200: {"content": {"application/json": {"example": [{
                             "id": "ord_123",
                             "order_number": "DRZ-2024-001234",
                             "customer_id": "usr_789",
                             "seller_id": "sel_456",
                             "seller_name": "Best Electronics BD",
                             "items": [{"id": "item_1", "product_id": "prod_123", "product_title": "Wireless Earbuds", "product_image": "https://cdn.daraz.com/p1.jpg", "variation": "Black", "price": 1200, "quantity": 2, "subtotal": 2400}],
                             "shipping_address": {"id": "addr_1", "full_name": "Customer Name", "phone": "01712345678", "region": "Dhaka", "city": "Dhaka", "area": "Gulshan", "address": "House 25", "landmark": None, "is_default": True, "label": "Home"},
                             "payment_method": "CASH_ON_DELIVERY",
                             "subtotal": 2400,
                             "shipping_fee": 60,
                             "voucher_discount": 0,
                             "total": 2460,
                             "status": "TO_SHIP",
                             "shipment_status": "PACKED",
                             "tracking_number": None,
                             "carrier": None,
                             "created_at": "2024-01-15T10:30:00",
                             "updated_at": "2024-01-15T14:00:00"
                         }]}}}})
async def get_seller_orders(
    status: Optional[OrderStatus] = Query(None),
    search: Optional[str] = Query(None, description="Search by order ID"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_seller)
):
    """Get seller orders (Orders page with filters). Requires Seller Bearer token."""
    return [{
        "id": "ord_123",
        "order_number": "DRZ-2024-001234",
        "customer_id": "usr_789",
        "seller_id": "sel_456",
        "seller_name": "Best Electronics BD",
        "items": [{"id": "item_1", "product_id": "prod_123", "product_title": "Wireless Earbuds", "product_image": "https://cdn.daraz.com/p1.jpg", "variation": "Black", "price": 1200, "quantity": 2, "subtotal": 2400}],
        "shipping_address": {"id": "addr_1", "full_name": "Customer Name", "phone": "01712345678", "region": "Dhaka", "city": "Dhaka", "area": "Gulshan", "address": "House 25", "landmark": None, "is_default": True, "label": "Home"},
        "payment_method": "CASH_ON_DELIVERY",
        "subtotal": 2400,
        "shipping_fee": 60,
        "voucher_discount": 0,
        "total": 2460,
        "status": "TO_SHIP",
        "shipment_status": "PACKED",
        "tracking_number": None,
        "carrier": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }]

@seller_orders_router.put("/{order_id}/status", response_model=Order)
async def update_order_status(
    order_id: str = Path(..., example="ord_123"),
    update: SellerOrderUpdate = Body(..., example={
        "status": "TO_RECEIVE",
        "tracking_number": "TRK123456789",
        "carrier": "Daraz Express"
    }),
    current_user: CurrentUser = Depends(get_current_seller)
):
    """Update order status and add tracking (Update Product Status use case). Requires Seller Bearer token."""
    return {
        "id": order_id,
        "order_number": "DRZ-2024-001234",
        "customer_id": "usr_789",
        "seller_id": "sel_456",
        "seller_name": "Best Electronics BD",
        "items": [{"id": "item_1", "product_id": "prod_123", "product_title": "Wireless Earbuds", "product_image": "https://cdn.daraz.com/p1.jpg", "variation": "Black", "price": 1200, "quantity": 2, "subtotal": 2400}],
        "shipping_address": {"id": "addr_1", "full_name": "Customer Name", "phone": "01712345678", "region": "Dhaka", "city": "Dhaka", "area": "Gulshan", "address": "House 25", "landmark": None, "is_default": True, "label": "Home"},
        "payment_method": "CASH_ON_DELIVERY",
        "subtotal": 2400,
        "shipping_fee": 60,
        "voucher_discount": 0,
        "total": 2460,
        "status": "TO_RECEIVE",
        "shipment_status": "SHIPPED",
        "tracking_number": "TRK123456789",
        "carrier": "Daraz Express",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

@seller_orders_router.post("/{order_id}/request-rider", response_model=MessageResponse)
async def request_rider(
    order_id: str = Path(..., example="ord_123"),
    pickup_address_id: str = Body(..., embed=True, example="addr_warehouse_1"),
    current_user: CurrentUser = Depends(get_current_seller)
):
    """Request rider for delivery (Request Rider use case - includes Inform delivery location). Requires Seller Bearer token."""
    return {"status": "success", "message": "Rider requested. Pickup scheduled."}

# Seller Returns Router
seller_returns_router = APIRouter(prefix="/v1/seller/returns", tags=["Seller-Returns"])

@seller_returns_router.get("", response_model=List[Return],
                          responses={200: {"content": {"application/json": {"example": [{
                              "id": "ret_123",
                              "return_number": "RET-2024-0001",
                              "order_id": "ord_123",
                              "order_number": "DRZ-2024-001234",
                              "product_id": "prod_789",
                              "product_title": "Wireless Earbuds",
                              "product_image": "https://cdn.daraz.com/p1.jpg",
                              "reason": "DAMAGED",
                              "description": "Product case was broken",
                              "images": ["https://cdn.daraz.com/returns/d1.jpg"],
                              "status": "REQUESTED",
                              "refund_amount": 1200,
                              "refund_method": "BKASH",
                              "created_at": "2024-01-15T10:00:00",
                              "updated_at": "2024-01-15T10:00:00"
                          }]}}}})
async def get_seller_returns(
    status: Optional[ReturnStatus] = Query(None),
    current_user: CurrentUser = Depends(get_current_seller)
):
    """Get return requests for seller (Return Orders page). Requires Seller Bearer token."""
    return [{
        "id": "ret_123",
        "return_number": "RET-2024-0001",
        "order_id": "ord_123",
        "order_number": "DRZ-2024-001234",
        "product_id": "prod_789",
        "product_title": "Wireless Earbuds",
        "product_image": "https://cdn.daraz.com/p1.jpg",
        "reason": "DAMAGED",
        "description": "Product case was broken",
        "images": ["https://cdn.daraz.com/returns/d1.jpg"],
        "status": "REQUESTED",
        "refund_amount": 1200,
        "refund_method": "BKASH",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }]

@seller_returns_router.put("/{return_id}/decide", response_model=Return)
async def decide_return(
    return_id: str = Path(..., example="ret_123"),
    decision: ReturnDecision = Body(..., example={"approved": True, "reason": None}),
    current_user: CurrentUser = Depends(get_current_seller)
):
    """Approve or reject return request (Return Amount use case - includes Process Refund). Requires Seller Bearer token."""
    return {
        "id": return_id,
        "return_number": "RET-2024-0001",
        "order_id": "ord_123",
        "order_number": "DRZ-2024-001234",
        "product_id": "prod_789",
        "product_title": "Wireless Earbuds",
        "product_image": "https://cdn.daraz.com/p1.jpg",
        "reason": "DAMAGED",
        "description": "Product case was broken",
        "images": ["https://cdn.daraz.com/returns/d1.jpg"],
        "status": "APPROVED",
        "refund_amount": 1200,
        "refund_method": "BKASH",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

# Seller Promotions Router
seller_promotions_router = APIRouter(prefix="/v1/seller/promotions", tags=["Seller-Promotions"])

@seller_promotions_router.get("/vouchers", response_model=List[Voucher],
                             responses={200: {"content": {"application/json": {"example": [{
                                 "id": "voucher_1",
                                 "code": "SAVE100",
                                 "discount_type": "fixed",
                                 "discount_value": 100,
                                 "min_purchase": 500,
                                 "max_discount": None,
                                 "start_date": "2024-01-01T00:00:00",
                                 "end_date": "2024-01-31T23:59:59",
                                 "usage_limit": 1000,
                                 "used_count": 250,
                                 "status": "active",
                                 "applicable_products": []
                             }]}}}})
async def get_vouchers(current_user: CurrentUser = Depends(get_current_seller)):
    """Get seller vouchers (Promotions page - Vouchers tab). Requires Seller Bearer token."""
    return [{
        "id": "voucher_1",
        "code": "SAVE100",
        "discount_type": "fixed",
        "discount_value": 100,
        "min_purchase": 500,
        "max_discount": None,
        "start_date": datetime.now(),
        "end_date": datetime.now() + timedelta(days=30),
        "usage_limit": 1000,
        "used_count": 250,
        "status": "active",
        "applicable_products": []
    }]

@seller_promotions_router.post("/vouchers", response_model=Voucher, status_code=status.HTTP_201_CREATED)
async def create_voucher(
    voucher: VoucherCreate = Body(..., example={
        "code": "NEWDEAL20",
        "discount_type": "percentage",
        "discount_value": 20,
        "min_purchase": 1000,
        "max_discount": 500,
        "start_date": "2024-02-01T00:00:00",
        "end_date": "2024-02-28T23:59:59",
        "usage_limit": 500,
        "applicable_products": []
    }),
    current_user: CurrentUser = Depends(get_current_seller)
):
    """Create new voucher (Advertise Promo/Offer use case). Requires Seller Bearer token."""
    return {
        "id": "voucher_new",
        "code": voucher.code,
        "discount_type": voucher.discount_type,
        "discount_value": voucher.discount_value,
        "min_purchase": voucher.min_purchase,
        "max_discount": voucher.max_discount,
        "start_date": voucher.start_date,
        "end_date": voucher.end_date,
        "usage_limit": voucher.usage_limit,
        "used_count": 0,
        "status": "active",
        "applicable_products": voucher.applicable_products
    }

@seller_promotions_router.get("/campaigns", response_model=List[Campaign])
async def get_campaigns(current_user: CurrentUser = Depends(get_current_seller)):
    """Get seller campaigns (Promote Products use case). Requires Seller Bearer token."""
    return [{
        "id": "camp_1",
        "name": "January Sale",
        "description": "New Year special discounts",
        "start_date": datetime.now(),
        "end_date": datetime.now() + timedelta(days=15),
        "discount_percentage": 15,
        "products_count": 25,
        "status": "active",
        "total_sales": 125000.00
    }]

@seller_promotions_router.post("/campaigns", response_model=Campaign, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign: CampaignCreate = Body(..., example={
        "name": "February Flash",
        "description": "Limited time offers",
        "start_date": "2024-02-01T00:00:00",
        "end_date": "2024-02-07T23:59:59",
        "discount_percentage": 25,
        "product_ids": ["prod_123", "prod_456"]
    }),
    current_user: CurrentUser = Depends(get_current_seller)
):
    """Create new campaign (Promote Products use case). Requires Seller Bearer token."""
    return {
        "id": "camp_new",
        "name": campaign.name,
        "description": campaign.description,
        "start_date": campaign.start_date,
        "end_date": campaign.end_date,
        "discount_percentage": campaign.discount_percentage,
        "products_count": len(campaign.product_ids),
        "status": "pending",
        "total_sales": 0
    }

# Seller Income Router
seller_income_router = APIRouter(prefix="/v1/seller/income", tags=["Seller-Income"])

@seller_income_router.get("", response_model=SellerIncome,
                         responses={200: {"content": {"application/json": {"example": {
                             "overview": {
                                 "available_balance": 45000.00,
                                 "pending_balance": 12500.00,
                                 "total_withdrawn": 150000.00,
                                 "this_month_earnings": 28500.00
                             },
                             "earnings_chart": [{"date": "2024-01-01", "earnings": 5200}, {"date": "2024-01-02", "earnings": 6800}],
                             "payout_history": [{
                                 "id": "pay_1",
                                 "amount": 25000,
                                 "method": "Bank Transfer",
                                 "account_details": "****1234",
                                 "status": "completed",
                                 "requested_at": "2024-01-10T10:00:00",
                                 "processed_at": "2024-01-11T14:00:00"
                             }]
                         }}}}})
async def get_income(current_user: CurrentUser = Depends(get_current_seller)):
    """Get seller income overview (My Income page - See Stats, View Earning use cases). Requires Seller Bearer token."""
    return {
        "overview": {
            "available_balance": 45000.00,
            "pending_balance": 12500.00,
            "total_withdrawn": 150000.00,
            "this_month_earnings": 28500.00
        },
        "earnings_chart": [{"date": "2024-01-01", "earnings": 5200}, {"date": "2024-01-02", "earnings": 6800}],
        "payout_history": [{
            "id": "pay_1",
            "amount": 25000,
            "method": "Bank Transfer",
            "account_details": "****1234",
            "status": "completed",
            "requested_at": datetime.now(),
            "processed_at": datetime.now()
        }]
    }

@seller_income_router.get("/stats", response_model=Dict[str, Any])
async def get_seller_stats(current_user: CurrentUser = Depends(get_current_seller)):
    """Get seller statistics (See Stats use case - extends View Earning, See Rating). Requires Seller Bearer token."""
    return {
        "rating": 4.7,
        "total_reviews": 1250,
        "positive_reviews_percentage": 94,
        "total_sales": 2850000.00,
        "total_orders": 3420,
        "repeat_customers": 680,
        "average_order_value": 833.33,
        "best_selling_products": [
            {"product_id": "prod_123", "title": "Wireless Earbuds", "units_sold": 450, "revenue": 540000}
        ],
        "monthly_performance": [
            {"month": "2024-01", "orders": 280, "revenue": 235000}
        ]
    }

@seller_income_router.post("/withdraw", response_model=PayoutRecord, status_code=status.HTTP_201_CREATED)
async def request_withdrawal(
    request: WithdrawalRequest = Body(..., example={
        "amount": 20000.00,
        "method": "bKash",
        "account_details": "01712345678"
    }),
    current_user: CurrentUser = Depends(get_current_seller)
):
    """Request withdrawal. Requires Seller Bearer token."""
    return {
        "id": "pay_new",
        "amount": request.amount,
        "method": request.method,
        "account_details": request.account_details,
        "status": "pending",
        "requested_at": datetime.now(),
        "processed_at": None
    }

# ====================== RIDER ROUTER ======================

rider_router = APIRouter(prefix="/v1/rider", tags=["Rider"])

@rider_router.get("/stats", response_model=RiderStats,
                 responses={200: {"content": {"application/json": {"example": {
                     "today_deliveries": 8,
                     "completed_deliveries": 6,
                     "pending_deliveries": 2,
                     "total_earnings_today": 480.00,
                     "rating": 4.8
                 }}}}})
async def get_rider_stats(current_user: CurrentUser = Depends(get_current_rider)):
    """Get rider daily statistics. Requires Rider Bearer token."""
    return {
        "today_deliveries": 8,
        "completed_deliveries": 6,
        "pending_deliveries": 2,
        "total_earnings_today": 480.00,
        "rating": 4.8
    }

@rider_router.get("/deliveries", response_model=List[DeliveryAssignment],
                 responses={200: {"content": {"application/json": {"example": [{
                     "id": "del_123",
                     "order_id": "ord_456",
                     "order_number": "DRZ-2024-001234",
                     "pickup_address": {"id": "addr_w1", "full_name": "Best Electronics BD", "phone": "01812345678", "region": "Dhaka", "city": "Dhaka", "area": "Uttara", "address": "Warehouse 5, Sector 10", "landmark": None, "is_default": False, "label": "Warehouse"},
                     "delivery_address": {"id": "addr_c1", "full_name": "John Doe", "phone": "01712345678", "region": "Dhaka", "city": "Dhaka", "area": "Gulshan", "address": "House 25, Road 103", "landmark": "Near City Bank", "is_default": True, "label": "Home"},
                     "customer_name": "John Doe",
                     "customer_phone": "01712345678",
                     "items_count": 2,
                     "payment_method": "CASH_ON_DELIVERY",
                     "cod_amount": 2460.00,
                     "status": "ASSIGNED",
                     "assigned_at": "2024-01-15T08:00:00",
                     "estimated_delivery": "2024-01-15T14:00:00"
                 }]}}}})
async def get_deliveries(
    status: Optional[DeliveryStatus] = Query(None),
    current_user: CurrentUser = Depends(get_current_rider)
):
    """Get assigned deliveries. Requires Rider Bearer token."""
    return [{
        "id": "del_123",
        "order_id": "ord_456",
        "order_number": "DRZ-2024-001234",
        "pickup_address": {"id": "addr_w1", "full_name": "Best Electronics BD", "phone": "01812345678", "region": "Dhaka", "city": "Dhaka", "area": "Uttara", "address": "Warehouse 5, Sector 10", "landmark": None, "is_default": False, "label": "Warehouse"},
        "delivery_address": {"id": "addr_c1", "full_name": "John Doe", "phone": "01712345678", "region": "Dhaka", "city": "Dhaka", "area": "Gulshan", "address": "House 25, Road 103", "landmark": "Near City Bank", "is_default": True, "label": "Home"},
        "customer_name": "John Doe",
        "customer_phone": "01712345678",
        "items_count": 2,
        "payment_method": "CASH_ON_DELIVERY",
        "cod_amount": 2460.00,
        "status": "ASSIGNED",
        "assigned_at": datetime.now(),
        "estimated_delivery": datetime.now() + timedelta(hours=6)
    }]

@rider_router.put("/deliveries/{delivery_id}/status", response_model=DeliveryAssignment)
async def update_delivery_status(
    delivery_id: str = Path(..., example="del_123"),
    update: DeliveryStatusUpdate = Body(..., example={
        "status": "DELIVERED",
        "notes": "Delivered to customer",
        "proof_image": "https://cdn.daraz.com/proofs/del_123.jpg",
        "recipient_name": "John Doe"
    }),
    current_user: CurrentUser = Depends(get_current_rider)
):
    """Update delivery status (Update Product Status use case from Rider). Requires Rider Bearer token."""
    return {
        "id": delivery_id,
        "order_id": "ord_456",
        "order_number": "DRZ-2024-001234",
        "pickup_address": {"id": "addr_w1", "full_name": "Best Electronics BD", "phone": "01812345678", "region": "Dhaka", "city": "Dhaka", "area": "Uttara", "address": "Warehouse 5, Sector 10", "landmark": None, "is_default": False, "label": "Warehouse"},
        "delivery_address": {"id": "addr_c1", "full_name": "John Doe", "phone": "01712345678", "region": "Dhaka", "city": "Dhaka", "area": "Gulshan", "address": "House 25, Road 103", "landmark": "Near City Bank", "is_default": True, "label": "Home"},
        "customer_name": "John Doe",
        "customer_phone": "01712345678",
        "items_count": 2,
        "payment_method": "CASH_ON_DELIVERY",
        "cod_amount": 2460.00,
        "status": "DELIVERED",
        "assigned_at": datetime.now(),
        "estimated_delivery": datetime.now()
    }

@rider_router.post("/deliveries/{delivery_id}/contact-customer", response_model=MessageResponse)
async def contact_customer(
    delivery_id: str = Path(..., example="del_123"),
    message: str = Body(..., embed=True, example="I am arriving in 10 minutes."),
    current_user: CurrentUser = Depends(get_current_rider)
):
    """Contact customer for delivery (Contact Customer For Delivery use case). Requires Rider Bearer token."""
    return {"status": "success", "message": "Customer notified via SMS."}

# ====================== PICKUP POINT ROUTER ======================

pickup_point_router = APIRouter(prefix="/v1/pickup-point", tags=["PickupPoint"])

@pickup_point_router.get("/stats", response_model=PickupPointStats,
                        responses={200: {"content": {"application/json": {"example": {
                            "pending_pickups": 5,
                            "ready_for_pickup": 12,
                            "picked_up_today": 8,
                            "expired_orders": 2
                        }}}}})
async def get_pickup_point_stats(current_user: CurrentUser = Depends(get_current_pickup_point)):
    """Get pickup point statistics. Requires Pickup Point Bearer token."""
    return {
        "pending_pickups": 5,
        "ready_for_pickup": 12,
        "picked_up_today": 8,
        "expired_orders": 2
    }

@pickup_point_router.get("/orders", response_model=List[PickupOrder],
                        responses={200: {"content": {"application/json": {"example": [{
                            "id": "pickup_123",
                            "order_id": "ord_456",
                            "order_number": "DRZ-2024-001234",
                            "customer_name": "John Doe",
                            "customer_phone": "01712345678",
                            "items_count": 2,
                            "status": "READY_FOR_PICKUP",
                            "arrived_at": "2024-01-15T10:00:00",
                            "pickup_code": "ABC123",
                            "expires_at": "2024-01-20T23:59:59"
                        }]}}}})
async def get_pickup_orders(
    status: Optional[PickupStatus] = Query(None),
    current_user: CurrentUser = Depends(get_current_pickup_point)
):
    """Get orders at pickup point. Requires Pickup Point Bearer token."""
    return [{
        "id": "pickup_123",
        "order_id": "ord_456",
        "order_number": "DRZ-2024-001234",
        "customer_name": "John Doe",
        "customer_phone": "01712345678",
        "items_count": 2,
        "status": "READY_FOR_PICKUP",
        "arrived_at": datetime.now(),
        "pickup_code": "ABC123",
        "expires_at": datetime.now() + timedelta(days=5)
    }]

@pickup_point_router.put("/orders/{pickup_id}/status", response_model=PickupOrder)
async def update_pickup_status(
    pickup_id: str = Path(..., example="pickup_123"),
    update: PickupStatusUpdate = Body(..., example={
        "status": "PICKED_UP",
        "notes": "Customer collected with valid ID"
    }),
    current_user: CurrentUser = Depends(get_current_pickup_point)
):
    """Update pickup order status (Update Shipping Status use case). Requires PickupPoint Bearer token."""
    return {
        "id": pickup_id,
        "order_id": "ord_456",
        "order_number": "DRZ-2024-001234",
        "customer_name": "John Doe",
        "customer_phone": "01712345678",
        "items_count": 2,
        "status": "PICKED_UP",
        "arrived_at": datetime.now(),
        "pickup_code": "ABC123",
        "expires_at": datetime.now() + timedelta(days=5)
    }

@pickup_point_router.post("/orders/{pickup_id}/contact-customer", response_model=MessageResponse)
async def contact_customer_for_pickup(
    pickup_id: str = Path(..., example="pickup_123"),
    message: str = Body(..., embed=True, example="Your order is ready for pickup. Please collect within 5 days."),
    current_user: CurrentUser = Depends(get_current_pickup_point)
):
    """Contact customer for pickup (Contact Customer For Pickup use case). Requires PickupPoint Bearer token."""
    return {"status": "success", "message": "Customer notified via SMS."}

# ====================== ADMIN MODELS ======================

class ProductVerificationStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class ProductVerificationRequest(BaseModel):
    product_id: str
    status: ProductVerificationStatus
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None

class ProductVerificationRecord(BaseModel):
    id: str
    product_id: str
    product_title: str
    seller_id: str
    seller_name: str
    submitted_at: datetime
    status: ProductVerificationStatus
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None

class DisputeStatus(str, Enum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED_CUSTOMER_FAVOR = "RESOLVED_CUSTOMER_FAVOR"
    RESOLVED_SELLER_FAVOR = "RESOLVED_SELLER_FAVOR"
    CLOSED = "CLOSED"

class ReturnDispute(BaseModel):
    id: str
    return_id: str
    return_number: str
    order_id: str
    customer_id: str
    customer_name: str
    seller_id: str
    seller_name: str
    product_title: str
    dispute_reason: str
    customer_evidence: List[str]
    seller_response: Optional[str] = None
    seller_evidence: List[str] = []
    status: DisputeStatus
    admin_notes: Optional[str] = None
    resolution: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class DisputeResolution(BaseModel):
    status: DisputeStatus
    resolution: str
    admin_notes: Optional[str] = None
    refund_amount: Optional[float] = None

class AdminDashboard(BaseModel):
    pending_verifications: int
    open_disputes: int
    total_products_verified_today: int
    total_disputes_resolved_today: int
    recent_verifications: List[ProductVerificationRecord]
    recent_disputes: List[ReturnDispute]

# ====================== ADMIN ROUTER ======================

admin_router = APIRouter(prefix="/v1/admin", tags=["Admin"])

@admin_router.post("/login", response_model=Token,
                  responses={200: {"content": {"application/json": {"example": {
                      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbl8xMjMiLCJyb2xlIjoiQURNSU4ifQ.admin_signature",
                      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbl8xMjMiLCJ0eXBlIjoicmVmcmVzaCJ9.admin_refresh",
                      "token_type": "bearer",
                      "user_role": "ADMIN",
                      "expires_in": 1800
                  }}}}})
async def admin_login(credentials: UserLogin = Body(..., example={"email": "admin@daraz.com", "password": "adminSecure123"})):
    """
    Admin login endpoint.
    
    - Only users with ADMIN role can login through this endpoint
    - Returns JWT tokens for admin operations
    """
    return {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbl8xMjMifQ.admin",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbl8xMjMifQ.refresh",
        "token_type": "bearer",
        "user_role": "ADMIN",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@admin_router.get("/dashboard", response_model=AdminDashboard,
                 responses={200: {"content": {"application/json": {"example": {
                     "pending_verifications": 15,
                     "open_disputes": 8,
                     "total_products_verified_today": 45,
                     "total_disputes_resolved_today": 12,
                     "recent_verifications": [],
                     "recent_disputes": []
                 }}}}})
async def get_admin_dashboard(current_user: CurrentUser = Depends(get_current_admin)):
    """Get admin dashboard overview. Requires Admin token."""
    return {
        "pending_verifications": 15,
        "open_disputes": 8,
        "total_products_verified_today": 45,
        "total_disputes_resolved_today": 12,
        "recent_verifications": [],
        "recent_disputes": []
    }

# ====================== PRODUCT QUALITY VERIFICATION ======================

@admin_router.get("/products/pending-verification", response_model=List[ProductVerificationRecord],
                 responses={200: {"content": {"application/json": {"example": [{
                     "id": "ver_123",
                     "product_id": "prod_456",
                     "product_title": "Wireless Bluetooth Earbuds",
                     "seller_id": "sel_789",
                     "seller_name": "Best Electronics BD",
                     "submitted_at": "2024-01-15T10:00:00",
                     "status": "PENDING",
                     "reviewed_by": None,
                     "reviewed_at": None,
                     "rejection_reason": None,
                     "notes": None
                 }]}}}})
async def get_pending_verifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Get list of products pending quality verification. Requires Admin token."""
    return [{
        "id": "ver_123",
        "product_id": "prod_456",
        "product_title": "Wireless Bluetooth Earbuds",
        "seller_id": "sel_789",
        "seller_name": "Best Electronics BD",
        "submitted_at": datetime.now(),
        "status": "PENDING",
        "reviewed_by": None,
        "reviewed_at": None,
        "rejection_reason": None,
        "notes": None
    }]

@admin_router.get("/products/verification/{product_id}", response_model=ProductVerificationRecord,
                 responses={200: {"content": {"application/json": {"example": {
                     "id": "ver_123",
                     "product_id": "prod_456",
                     "product_title": "Wireless Bluetooth Earbuds",
                     "seller_id": "sel_789",
                     "seller_name": "Best Electronics BD",
                     "submitted_at": "2024-01-15T10:00:00",
                     "status": "PENDING",
                     "reviewed_by": None,
                     "reviewed_at": None,
                     "rejection_reason": None,
                     "notes": None
                 }}}}})
async def get_product_verification_details(
    product_id: str = Path(..., example="prod_456"),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Get product verification details. Requires Admin token."""
    return {
        "id": "ver_123",
        "product_id": product_id,
        "product_title": "Wireless Bluetooth Earbuds",
        "seller_id": "sel_789",
        "seller_name": "Best Electronics BD",
        "submitted_at": datetime.now(),
        "status": "PENDING",
        "reviewed_by": None,
        "reviewed_at": None,
        "rejection_reason": None,
        "notes": None
    }

@admin_router.post("/products/verify", response_model=ProductVerificationRecord,
                  responses={
                      200: {"content": {"application/json": {"example": {
                          "id": "ver_123",
                          "product_id": "prod_456",
                          "product_title": "Wireless Bluetooth Earbuds",
                          "seller_id": "sel_789",
                          "seller_name": "Best Electronics BD",
                          "submitted_at": "2024-01-15T10:00:00",
                          "status": "APPROVED",
                          "reviewed_by": "admin_001",
                          "reviewed_at": "2024-01-15T14:30:00",
                          "rejection_reason": None,
                          "notes": "Product meets quality standards"
                      }}}},
                      400: {"content": {"application/json": {"example": {"detail": "Rejection reason required when rejecting a product"}}}}
                  })
async def verify_product(
    verification: ProductVerificationRequest = Body(..., example={
        "product_id": "prod_456",
        "status": "APPROVED",
        "rejection_reason": None,
        "notes": "Product meets quality standards"
    }),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """
    Approve or reject a product for quality verification.
    
    - **APPROVED**: Product will be listed on the marketplace
    - **REJECTED**: Product will be sent back to seller with rejection reason
    
    Requires Admin token.
    """
    return {
        "id": "ver_123",
        "product_id": verification.product_id,
        "product_title": "Wireless Bluetooth Earbuds",
        "seller_id": "sel_789",
        "seller_name": "Best Electronics BD",
        "submitted_at": datetime.now() - timedelta(hours=4),
        "status": verification.status,
        "reviewed_by": current_user.user_id,
        "reviewed_at": datetime.now(),
        "rejection_reason": verification.rejection_reason,
        "notes": verification.notes
    }

# ====================== RETURN REQUEST DISPUTE ======================

@admin_router.get("/disputes", response_model=List[ReturnDispute],
                 responses={200: {"content": {"application/json": {"example": [{
                     "id": "disp_123",
                     "return_id": "ret_456",
                     "return_number": "RET-2024-0001",
                     "order_id": "ord_789",
                     "customer_id": "usr_111",
                     "customer_name": "John Doe",
                     "seller_id": "sel_222",
                     "seller_name": "Best Electronics BD",
                     "product_title": "Wireless Earbuds",
                     "dispute_reason": "Seller rejected return claiming product was damaged by customer",
                     "customer_evidence": ["https://cdn.daraz.com/evidence/img1.jpg"],
                     "seller_response": "Product was not in original packaging",
                     "seller_evidence": ["https://cdn.daraz.com/evidence/seller_img1.jpg"],
                     "status": "OPEN",
                     "admin_notes": None,
                     "resolution": None,
                     "created_at": "2024-01-15T10:00:00",
                     "updated_at": "2024-01-15T10:00:00"
                 }]}}}})
async def get_disputes(
    status: Optional[DisputeStatus] = Query(None, description="Filter by dispute status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Get list of return disputes. Requires Admin token."""
    return [{
        "id": "disp_123",
        "return_id": "ret_456",
        "return_number": "RET-2024-0001",
        "order_id": "ord_789",
        "customer_id": "usr_111",
        "customer_name": "John Doe",
        "seller_id": "sel_222",
        "seller_name": "Best Electronics BD",
        "product_title": "Wireless Earbuds",
        "dispute_reason": "Seller rejected return claiming product was damaged by customer",
        "customer_evidence": ["https://cdn.daraz.com/evidence/img1.jpg"],
        "seller_response": "Product was not in original packaging",
        "seller_evidence": ["https://cdn.daraz.com/evidence/seller_img1.jpg"],
        "status": "OPEN",
        "admin_notes": None,
        "resolution": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }]

@admin_router.get("/disputes/{dispute_id}", response_model=ReturnDispute,
                 responses={200: {"content": {"application/json": {"example": {
                     "id": "disp_123",
                     "return_id": "ret_456",
                     "return_number": "RET-2024-0001",
                     "order_id": "ord_789",
                     "customer_id": "usr_111",
                     "customer_name": "John Doe",
                     "seller_id": "sel_222",
                     "seller_name": "Best Electronics BD",
                     "product_title": "Wireless Earbuds",
                     "dispute_reason": "Seller rejected return claiming product was damaged by customer",
                     "customer_evidence": ["https://cdn.daraz.com/evidence/img1.jpg", "https://cdn.daraz.com/evidence/img2.jpg"],
                     "seller_response": "Product was not in original packaging when received",
                     "seller_evidence": ["https://cdn.daraz.com/evidence/seller_img1.jpg"],
                     "status": "UNDER_REVIEW",
                     "admin_notes": "Reviewing evidence from both parties",
                     "resolution": None,
                     "created_at": "2024-01-15T10:00:00",
                     "updated_at": "2024-01-16T09:00:00"
                 }}}}})
async def get_dispute_details(
    dispute_id: str = Path(..., example="disp_123"),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Get dispute details with all evidence. Requires Admin token."""
    return {
        "id": dispute_id,
        "return_id": "ret_456",
        "return_number": "RET-2024-0001",
        "order_id": "ord_789",
        "customer_id": "usr_111",
        "customer_name": "John Doe",
        "seller_id": "sel_222",
        "seller_name": "Best Electronics BD",
        "product_title": "Wireless Earbuds",
        "dispute_reason": "Seller rejected return claiming product was damaged by customer",
        "customer_evidence": ["https://cdn.daraz.com/evidence/img1.jpg", "https://cdn.daraz.com/evidence/img2.jpg"],
        "seller_response": "Product was not in original packaging when received",
        "seller_evidence": ["https://cdn.daraz.com/evidence/seller_img1.jpg"],
        "status": "UNDER_REVIEW",
        "admin_notes": "Reviewing evidence from both parties",
        "resolution": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

@admin_router.put("/disputes/{dispute_id}/resolve", response_model=ReturnDispute,
                 responses={
                     200: {"content": {"application/json": {"example": {
                         "id": "disp_123",
                         "return_id": "ret_456",
                         "return_number": "RET-2024-0001",
                         "order_id": "ord_789",
                         "customer_id": "usr_111",
                         "customer_name": "John Doe",
                         "seller_id": "sel_222",
                         "seller_name": "Best Electronics BD",
                         "product_title": "Wireless Earbuds",
                         "dispute_reason": "Seller rejected return claiming product was damaged by customer",
                         "customer_evidence": ["https://cdn.daraz.com/evidence/img1.jpg"],
                         "seller_response": "Product was not in original packaging",
                         "seller_evidence": ["https://cdn.daraz.com/evidence/seller_img1.jpg"],
                         "status": "RESOLVED_CUSTOMER_FAVOR",
                         "admin_notes": "Evidence shows product was received damaged from shipping",
                         "resolution": "Full refund to customer. Shipping insurance claim initiated.",
                         "created_at": "2024-01-15T10:00:00",
                         "updated_at": "2024-01-17T11:30:00"
                     }}}}
                 })
async def resolve_dispute(
    dispute_id: str = Path(..., example="disp_123"),
    resolution: DisputeResolution = Body(..., example={
        "status": "RESOLVED_CUSTOMER_FAVOR",
        "resolution": "Full refund to customer. Shipping insurance claim initiated.",
        "admin_notes": "Evidence shows product was received damaged from shipping",
        "refund_amount": 1200.00
    }),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """
    Resolve a return dispute.
    
    Resolution options:
    - **RESOLVED_CUSTOMER_FAVOR**: Approve return and process refund
    - **RESOLVED_SELLER_FAVOR**: Reject return request
    - **CLOSED**: Close without action (e.g., customer withdrew complaint)
    
    Requires Admin token.
    """
    return {
        "id": dispute_id,
        "return_id": "ret_456",
        "return_number": "RET-2024-0001",
        "order_id": "ord_789",
        "customer_id": "usr_111",
        "customer_name": "John Doe",
        "seller_id": "sel_222",
        "seller_name": "Best Electronics BD",
        "product_title": "Wireless Earbuds",
        "dispute_reason": "Seller rejected return claiming product was damaged by customer",
        "customer_evidence": ["https://cdn.daraz.com/evidence/img1.jpg"],
        "seller_response": "Product was not in original packaging",
        "seller_evidence": ["https://cdn.daraz.com/evidence/seller_img1.jpg"],
        "status": resolution.status,
        "admin_notes": resolution.admin_notes,
        "resolution": resolution.resolution,
        "created_at": datetime.now() - timedelta(days=2),
        "updated_at": datetime.now()
    }

@admin_router.post("/disputes/{dispute_id}/add-notes", response_model=MessageResponse)
async def add_dispute_notes(
    dispute_id: str = Path(..., example="disp_123"),
    notes: str = Body(..., embed=True, example="Contacted seller for additional documentation"),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Add internal notes to a dispute. Requires Admin token."""
    return {"status": "success", "message": "Notes added to dispute."}

# ====================== REGISTER ROUTERS ======================

app.include_router(auth_router)
app.include_router(account_router)
app.include_router(orders_router)
app.include_router(cart_router)
app.include_router(wishlist_router)
app.include_router(reviews_router)
app.include_router(returns_router)
app.include_router(products_router)
app.include_router(seller_dashboard_router)
app.include_router(seller_products_router)
app.include_router(seller_orders_router)
app.include_router(seller_returns_router)
app.include_router(seller_promotions_router)
app.include_router(seller_income_router)
app.include_router(rider_router)
app.include_router(pickup_point_router)
app.include_router(admin_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
