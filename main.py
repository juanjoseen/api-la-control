from fastapi import Depends, FastAPI, HTTPException, status
import uuid
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime
from auth import *
from models import *
from database import *
from sqlalchemy.orm import Session

app = FastAPI()

# uvicorn main:app --reload

@app.get("/")
async def root():
    return {"isAlive": True}

@app.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> TokenResponse:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        return TokenResponse(success=False, message=ErrorType.INCORRECT_USER_OR_PASSWORD.value)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})
    return TokenResponse(success=True, data=Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer"))

@app.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(refresh_token: str) -> TokenResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("token_type")
        
        if username is None or token_type != "refresh":
            raise credentials_exception
            
        user = get_user(username)
        if user is None:
            raise credentials_exception
            
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(data={"sub": user.username})
        return TokenResponse(success=True, data=Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer"))
    except jwt.PyJWTError:
        raise credentials_exception

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]) -> UserResponse:
    if current_user:
        return UserResponse(success=True, data=current_user)
    else:
        return UserResponse(success=False, message=ErrorType.USER_DOES_NOT_EXIST.value)

@app.post("/users", response_model=TokenResponse)
async def create_user(data: UserIn, db: Session = Depends(get_db)) -> TokenResponse:
    user = create_new_user(db, data)
    if not user:
        return TokenResponse(success=False, message=ErrorType.USER_ALREADY_EXISTS.value)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})
    return TokenResponse(success=True, data=Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer"))

# Addresses Endpoints

@app.post("/addresses", response_model=AddressResponse)
async def create_address(address: AddressCreate, db: Session = Depends(get_db)):
    return new_address(db, address)

@app.get("/addresses", response_model=AddressListResponse)
async def read_addresses(db: Session = Depends(get_db)):
    return get_all_addresses(db)

@app.get("/addresses/{address_id}", response_model=AddressResponse)
async def read_address(address_id: int, db: Session = Depends(get_db)):
    return get_address(db, address_id)

@app.put("/addresses/{address_id}", response_model=AddressResponse)
async def update_address(address_id: int, address: AddressCreate, db: Session = Depends(get_db)):
    return update_db_address(db, address_id, address)

@app.delete("/addresses/{address_id}", response_model=BoolResponse)
async def delete_address(address_id: int, db: Session = Depends(get_db)):
    return delete_db_address(db, address_id)

# Orders Endpoints

@app.post("/order", response_model=BoolResponse)
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    return new_order(db=db, order=order)

@app.get("/orders", response_model=OrderListResponse)
async def read_orders(db: Session = Depends(get_db)):
    return get_all_orders(db)

@app.get("/order/{order_id}", response_model=OrderDetailsResponse)
async def read_order(order_id: str, db: Session = Depends(get_db)):
    return get_order_details(db, order_id)

@app.put("/order/{order_id}", response_model=BoolResponse)
async def update_order(order_id: str, order: OrderCreate, db: Session = Depends(get_db)):
    return update_order_data(db, order_id, order)

@app.delete("/order/{order_id}", response_model=BoolResponse)
async def delete_order(order_id: str, db: Session = Depends(get_db)):
    return delete_order_data(db, order_id)