import os
from fastapi import Depends
from models import *
from dotenv import load_dotenv
from sqlalchemy import create_engine
from pwdlib import PasswordHash
from sqlalchemy.orm import sessionmaker, Session

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
    db_user = DBUser(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        disabled=False,
        hashed_password=get_password_hash(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return User(username=db_user.username, email=db_user.email, full_name=db_user.full_name, disabled=db_user.disabled)

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user
