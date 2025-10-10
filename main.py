from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordRequestForm
from auth import *
from models import *
from database import *
from sqlalchemy.orm import Session

app = FastAPI()

@app.get("/")
async def root():
    return {"isAlive": True}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    return current_user

@app.post("/users/", response_model=User)
async def create_user(data: UserIn, db: Session = Depends(get_db)) -> User:
    return create_new_user(db, data)