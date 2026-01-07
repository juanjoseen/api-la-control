import os
import uuid
from models import *
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
from pwdlib import PasswordHash
from sqlalchemy.orm import sessionmaker, Session, joinedload
from fastapi import HTTPException, status

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment variables")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

if "sslmode" not in DATABASE_URL:
    sep = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL += f"{sep}sslmode=require"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
password_hash = PasswordHash.recommended()

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password):
    return password_hash.hash(password)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user(username: str):
    with SessionLocal() as db:
        return db.query(DBUser).filter(DBUser.username == username).first()

def create_new_user(db: Session, user: UserIn) -> User:
    if get_user(user.username):
        return None
    db_user = DBUser(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        disabled=False,
        hashed_password=get_password_hash(user.password),
        profile_image=user.profile_image,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return User(username=db_user.username, email=db_user.email, full_name=db_user.full_name, disabled=db_user.disabled, profile_image=db_user.profile_image)

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def update_user_info(db: Session, username: str, user_update: UserUpdate) -> UserUpdateResponse:
    db_user = db.query(DBUser).filter(DBUser.username == username).first()
    if not db_user:
        return UserUpdateResponse(success=False, message=ErrorType.USER_DOES_NOT_EXIST.value)
    
    # Update only the fields that are provided
    if user_update.email is not None:
        db_user.email = user_update.email
    if user_update.full_name is not None:
        db_user.full_name = user_update.full_name
    if user_update.profile_image is not None:
        db_user.profile_image = user_update.profile_image
    
    db.commit()
    db.refresh(db_user)
    
    return UserUpdateResponse(
        success=True, 
        data=User(
            username=db_user.username, 
            email=db_user.email, 
            full_name=db_user.full_name, 
            disabled=db_user.disabled,
            profile_image=db_user.profile_image
        )
    )

def new_address(db: Session, address: AddressCreate) -> AddressResponse:
    db_address = DBAddress(**address.dict())
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    return AddressResponse(success=True, data=db_address)

def get_address(db: Session, address_id: int) -> AddressResponse:
    db_address = db.query(DBAddress).filter(DBAddress.id == address_id).first()
    if not db_address:
        return AddressResponse(success=False, message=ErrorType.ADDRESS_DOES_NOT_EXIST.value)
    return AddressResponse(success=True, data=db_address)

def get_all_addresses(db: Session) -> AddressListResponse:
    db_addresses = db.query(DBAddress).all()
    if not db_addresses:
        return AddressListResponse(success=False, message=ErrorType.NO_ADDRESS_FOUND.value)
    return AddressListResponse(success=True, data=db_addresses)

def update_db_address(db: Session, address_id: int, address: AddressCreate) -> AddressResponse:
    db_address = db.query(DBAddress).filter(DBAddress.id == address_id).first()
    if not db_address:
         return AddressResponse(success=False, message=ErrorType.ADDRESS_DOES_NOT_EXIST.value)
    for key, value in address.dict().items():
        setattr(db_address, key, value)
    db.commit()
    db.refresh(db_address)
    return AddressResponse(success=True, data=db_address)

def delete_db_address(db: Session, address_id: int) -> BoolResponse:
    db_address = db.query(DBAddress).filter(DBAddress.id == address_id).first()
    if not db_address:
         return BoolResponse(success=False, message=ErrorType.ADDRESS_DOES_NOT_EXIST.value)
    
    db.delete(db_address)
    db.commit()
    return BoolResponse(success=True, data=True)

def parse_deadline(date_str: str):
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except ValueError:
        # Fallback or error handling if format is wrong
        print(f"Error parsing date: {date_str}")
        try:
             return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
             raise HTTPException(status_code=400, detail="Invalid date format. Use DD/MM/YYYY")

def new_order(db: Session, order: OrderCreate) -> BoolResponse:
    shipping_address = db.query(DBAddress).filter(DBAddress.id == order.address_id).first()
    if not shipping_address:
        return BoolResponse(success=False, message=ErrorType.ADDRESS_DOES_NOT_EXIST.value)

    deadline_date = parse_deadline(order.deadline)

    db_order = DBOrder(
        id=uuid.uuid4(),
        client=order.title,
        product=order.product,
        deadline=deadline_date,
        address_id=shipping_address.id
    )
    db.add(db_order)
    
    # Add order items
    for item in order.order_items:
        db_item = DBOrderItem(
            order_id=db_order.id,
            size=item.size,
            amount=item.amount
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_order)
    return BoolResponse(success=True, data=True)

def update_order_data(db: Session, order_id: str, order: OrderCreate) -> BoolResponse:
    db_order = db.query(DBOrder).filter(DBOrder.id == order_id).first()
    if not db_order:
        return BoolResponse(success=False, message=ErrorType.ORDER_DOES_NOT_EXIST.value)
    
    db_order.client = order.title
    db_order.product = order.product
    db_order.deadline = parse_deadline(order.deadline)
    db_order.address_id = order.address_id

    # Update order items
    for item in order.order_items:
        db_item = db.query(DBOrderItem).filter(DBOrderItem.order_id == order_id, DBOrderItem.size == item.size).first()
        if not db_item:
            db_item = DBOrderItem(order_id=order_id, size=item.size, amount=item.amount)
            db.add(db_item)
        else:
            db_item.amount = item.amount
    
    db.commit()
    db.refresh(db_order)
    db.commit()
    db.refresh(db_order)
    return BoolResponse(success=True, data=True)

def delete_order_data(db: Session, order_id: str) -> BoolResponse:
    db_order = db.query(DBOrder).filter(DBOrder.id == order_id).first()
    if not db_order:
        return BoolResponse(success=False, message=ErrorType.ORDER_DOES_NOT_EXIST.value)
    
    # Manually delete items since relationship is viewonly or might not cascade
    db.query(DBOrderItem).filter(DBOrderItem.order_id == order_id).delete()
    
    db.delete(db_order)
    db.commit()
    return BoolResponse(success=True, data=True)

def get_all_orders(db: Session) -> OrderListResponse:
    orders = db.query(DBOrder).options(joinedload(DBOrder.address), joinedload(DBOrder.order_items)).all()
    # Map to Pydantic models with details
    # Pydantic's from_attributes should handle mapping if relationships are populated.
    # Note: DBOrder.items is a list of DBOrderItem. OrderWithDetails expects list[OrderItem].
    # OrderItem in models.py has size(enum) and amount(int). DBOrderItem has size(int) and amount(int).
    # Casting int to SizeType enum might happen automatically by Pydantic if defined as Enum.
    
    return OrderListResponse(success=True, data=orders)

def get_order_details(db: Session, order_id: str) -> OrderDetailsResponse:
    order = db.query(DBOrder).options(joinedload(DBOrder.address), joinedload(DBOrder.order_items)).filter(DBOrder.id == order_id).first()
    if not order:
        return OrderDetailsResponse(success=False, message=Error(code=404, message="Order not found"))
    return OrderDetailsResponse(success=True, data=order)