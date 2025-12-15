from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import DeclarativeBase
from enum import Enum
from typing import Optional

class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

    class Config:
        from_attributes = True

class UserIn(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    password: str

class UserInDB(User):
    hashed_password: str

    class Config:
        from_attributes = True

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

class Response(BaseModel):
    success: bool
    message: Optional[ErrorType] = None

class TokenResponse(Response):
    data: Optional[Token] = None

class UserResponse(Response):
    data: Optional[User] = None

# New Models for Addresses and Orders

class SizeType(str, Enum):
    XS = 'XS'
    S = 'S'
    M = 'M'
    L = 'L'
    XL = 'XL'
    XXL = 'XXL'
    XXXL = 'XXXL'

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

    id = Column(String, primary_key=True, index=True) # UUID stored as string or use UUID type if creating from scratch, but existing DB might expect specific type. Going with String for UUID for simplicity with SQLite/others if generic, but User said UUID primary key. Text/String is safest for minimal dependency issues unless psycopg generic UUID is desired.
    client = Column(String, nullable=False)
    product = Column(String, nullable=False)
    deadline = Column(String, nullable=False) # Date stored as string YYYY-MM-DD or use Date type.
    shipping_address = Column(Integer, nullable=False) # ForeignKey would be better but following strict table def first.
    
    # Relationships could be added here if needed, e.g.:
    # address_rel = relationship("DBAddress")

class DBOrderContent(Base):
    __tablename__ = "order_content"
    # SQLAlchemy requires a generic primary key or composite primary key.
    # We will use order_id and size as composite PK assuming unique size per order, or add a surrogate.
    # User SQL: no PK.
    order_id = Column(String, primary_key=True) 
    size = Column(String, primary_key=True) # Using String for ENUM storage in DB usually, or Enum type.
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
    deadline: str # ISO Date string
    shipping_address: int

class OrderCreate(OrderBase):
    contents: list[OrderContentCreate]

class Order(OrderBase):
    id: str
    # contents: list[OrderContent] = [] # Optional to include contents in response

    class Config:
        from_attributes = True

class AddressResponse(Response):
    data: Optional[Address] = None

class AddressListResponse(Response):
    data: list[Address] = []
    
class OrderResponse(Response):
    data: Optional[Order] = None

class OrderContentResponse(Response):
    data: Optional[OrderContent] = None

class BoolResponse(Response):
    data: bool
