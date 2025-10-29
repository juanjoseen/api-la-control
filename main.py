from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from auth import *
from models import *
from database import *
from sqlalchemy.orm import Session

app = FastAPI()

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
        return TokenResponse(success=True, data=Token(access_token=access_token, token_type="bearer"))
    except jwt.PyJWTError:
        raise credentials_exception

@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    return current_user

@app.post("/users/", response_model=TokenResponse)
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