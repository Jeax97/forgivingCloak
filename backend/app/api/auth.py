from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.models import User, AppSettings
from app.schemas import UserCreate, UserLogin, TokenResponse, TokenRefresh, UserResponse, SetupCheck
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/setup-check", response_model=SetupCheck)
def check_setup(db: Session = Depends(get_db)):
    """Check if initial setup is complete."""
    admin_exists = db.query(User).filter(User.is_admin.is_(True)).first() is not None
    setup_setting = db.query(AppSettings).filter(AppSettings.key == "setup_complete").first()
    is_complete = setup_setting is not None and setup_setting.value == "true"
    return SetupCheck(is_setup_complete=is_complete, has_admin_user=admin_exists)


@router.post("/setup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def initial_setup(data: UserCreate, db: Session = Depends(get_db)):
    """Create the first admin user. Only works if no admin exists."""
    existing_admin = db.query(User).filter(User.is_admin.is_(True)).first()
    if existing_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Setup already complete")

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        is_admin=True,
        is_active=True,
    )
    db.add(user)

    setup_flag = AppSettings(key="setup_complete", value="true")
    db.add(setup_flag)
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user (admin must exist first)."""
    if db.query(User).filter((User.email == data.email) | (User.username == data.username)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(data: TokenRefresh, db: Session = Depends(get_db)):
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
