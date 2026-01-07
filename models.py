from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, Date
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum
from typing import Optional, List
from datetime import date as date_type
import uuid

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    profile_image: Optional[str] = None

    class Config:
        from_attributes = True

class UserIn(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    password: str
    profile_image: Optional[str] = None

class UserInDB(User):
    hashed_password: str

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    profile_image: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Base(DeclarativeBase):
    pass

class DBUser(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    disabled = Column(Boolean, default=False)
    hashed_password = Column(String)
    profile_image = Column(String, nullable=True)

class Error(BaseModel):
    code: int
    message: str

class ErrorType(Enum):
    # User Errors
    USER_ALREADY_EXISTS = Error(code=1001, message="User already exists")
    USER_DOES_NOT_EXIST = Error(code=1002, message="User doesn't exist")

    # Authentication Errors
    INCORRECT_USER_OR_PASSWORD = Error(code=2001, message="Incorrect username or password")

    # JWT Errors
    INVALID_TOKEN = Error(code=3001, message="Invalid token")
    EXPIRED_TOKEN = Error(code=3002, message="Token expired")
    MISSING_TOKEN = Error(code=3003, message="Missing token")

    # Address Errors
    ADDRESS_DOES_NOT_EXIST = Error(code=4001, message="Address doesn't exist")
    ADDRESS_ALREADY_EXISTS = Error(code=4002, message="Address already exists")
    NO_ADDRESS_FOUND = Error(code=4003, message="No address found")

    # Order Errors
    ORDER_DOES_NOT_EXIST = Error(code=5001, message="Order doesn't exist")

class Response(BaseModel):
    success: bool
    message: Optional[Error] = None

class TokenResponse(Response):
    data: Optional[Token] = None

class UserResponse(Response):
    data: Optional[User] = None

class UserUpdateResponse(Response):
    data: Optional[User] = None

# New Models for Addresses and Orders

class SizeType(int, Enum):
    XS = 1
    S = 2
    M = 3
    L = 4
    XL = 5
    XXL = 6
    XXXL = 7

class DBAddress(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    recipient = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip_code = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)

class DBOrder(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    client = Column(String, nullable=False)
    product = Column(String, nullable=False)
    deadline = Column(Date, nullable=False)
    address_id = Column("shipping_address", Integer, nullable=False) # Maps to 'shipping_address' column
    
    # Relationships
    address = relationship("DBAddress", primaryjoin="DBOrder.address_id == DBAddress.id", foreign_keys=[address_id])
    order_items = relationship("DBOrderItem", primaryjoin="DBOrder.id == DBOrderItem.order_id", foreign_keys="DBOrderItem.order_id", viewonly=True)

class DBOrderItem(Base):
    __tablename__ = "order_items"
    
    # Composite primary key logic or surrogate key. 
    # Based on user request: order_id uuid NOT NULL, amount integer NOT NULL, size integer NOT NULL.
    # We might need a primary key for SQLAlchemy. Let's use a composite PK of order_id and size for now, 
    # unless we add a surrogate 'id'.
    # Given the table definition provided: TABLE "order_items" ("order_id" uuid NOT NULL, "amount" integer NOT NULL, "size" integer NOT NULL)
    # It doesn't explicitly state a PK. But SQLAlchemy ORM usually requires one.
    # I'll use order_id and size as composite PK assuming unique size per order is the intent, 
    # or just map it as is and let SQLA handle it (might be tricky without PK).
    # Let's assume (order_id, size) is unique enough for a PK for now to satisfy SQLAlchemy or add a surrogate if it fails.
    # Actually, often order items are just lines.
    
    order_id = Column(UUID(as_uuid=True), primary_key=True) 
    size = Column(Integer, primary_key=True) 
    amount = Column(Integer, nullable=False)

# Pydantic Schemas

class AddressBase(BaseModel):
    recipient: str
    phone: str
    address: str
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[int] = None
    notes: Optional[str] = None

class AddressCreate(AddressBase):
    recipient: str
    phone: str
    address: str
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[int] = None
    notes: Optional[str] = None

class Address(AddressBase):
    id: int

    class Config:
        from_attributes = True

class OrderContentBase(BaseModel):
    size: SizeType
    amount: int

class OrderContentCreate(OrderContentBase):
    pass

class OrderContent(OrderContentBase):
    order_id: str

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    client: str
    product: str
    deadline: date_type # Using date type
    address_id: int

class OrderItem(BaseModel):
    size: SizeType
    amount: int 

    class Config:
        from_attributes = True 

class OrderCreate(BaseModel):
    title: str
    product: str
    deadline: str
    address_id: int
    order_items: list[OrderItem]

class Order(OrderBase):
    id: uuid.UUID
    # contents: list[OrderContent] = [] # Optional to include contents in response

    class Config:
        from_attributes = True

class AddressResponse(Response):
    data: Optional[Address] = None

class AddressListResponse(Response):
    data: list[Address] = []
    
class OrderWithDetails(OrderBase):
    id: uuid.UUID # UUID type
    address: Optional[Address] = None
    order_items: List[OrderItem]

    class Config:
        from_attributes = True

class OrderResponse(Response):
    data: Optional[Order] = None

class OrderDetailsResponse(Response):
    data: Optional[OrderWithDetails] = None

class OrderListResponse(Response):
    data: List[OrderWithDetails] = []

class OrderContentResponse(Response):
    data: Optional[OrderContent] = None

class BoolResponse(Response):
    data: bool
