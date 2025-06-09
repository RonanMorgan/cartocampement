from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from .. import crud, models, schemas, security
from ..database import get_db # Import get_db from database.py

router = APIRouter()

# Dependency to get a DB session (REMOVED - now imported)
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False) # Set auto_error=False

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_name(db, name=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.name}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# This function will be used to protect endpoints
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials", # Default message if token is bad
        headers={"WWW-Authenticate": "Bearer"},
    )
    # If auto_error=False on oauth2_scheme, token can be None if not provided
    if not token:
        # Mimic FastAPI's default response when auto_error=True for missing token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except security.JWTError:
        raise credentials_exception

    user = crud.get_user_by_name(db, name=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_user_optional(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User | None:
    if not token: # If token is not provided by client, oauth2_scheme might make it None or raise error.
                  # However, OAuth2PasswordBearer by default requires a token.
                  # A truly optional scheme might need a custom one or careful handling if token is ""
                  # For now, let's assume if token is not passed or is invalid, we catch JWTError or it's None.
# With auto_error=False, if token is not present, 'token' param will be None.
        return None # Token is not present or malformed to the point oauth2_scheme returns None
    try:
        # At this point, 'token' should be a string if it was provided and parsable by the scheme.
        # If it was missing/malformed, 'token' would be None and we'd have returned above.
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None # No username in payload
        # We don't use schemas.TokenData here as we are not raising exception on validation error
    except security.JWTError:
        return None # Token is invalid (expired, wrong format, etc.)

    user = crud.get_user_by_name(db, name=username)
    if user is None:
        return None # User not found in DB
    return user
