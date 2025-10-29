from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import DeclarativeBase
from enum import Enum

class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

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
    message: ErrorType | None = None

class TokenResponse(Response):
    data: Token | None = None
