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

class Response(BaseModel):
    success: bool
    message: Optional[ErrorType] = None

class TokenResponse(Response):
    data: Optional[Token] = None

class UserResponse(Response):
    data: Optional[User] = None
