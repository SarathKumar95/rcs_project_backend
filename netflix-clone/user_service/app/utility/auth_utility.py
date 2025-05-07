import os
from fastapi import Response
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt



SECRET_KEY=os.getenv("SECRET_KEY")  # Use a secure secret key
ALGORITHM=os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



def set_auth_cookies(response: Response, access_token: str):
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,            # Set to False only in dev
        samesite="Lax",
        max_age=60 * 60 * 24 * 7  # 7 days
    )