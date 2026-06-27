"""
Authentication Router
Handles user registration, login, token refresh, and password reset.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    MessageResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user account.
    - Validates email uniqueness
    - Hashes password with bcrypt
    - Returns created user profile
    """
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == request.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Check phone uniqueness if provided
    if request.phone:
        existing_phone = await db.execute(select(User).where(User.phone == request.phone))
        if existing_phone.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this phone number already exists",
            )

    # Create new user
    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        phone=request.phone,
        language=request.language,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and return JWT access + refresh tokens.
    Supports both JSON request body and OAuth2 form data formats.
    """
    content_type = request.headers.get("content-type", "")
    email = None
    plain_password = None

    if "application/json" in content_type:
        try:
            body = await request.json()
            email = body.get("email")
            plain_password = body.get("password")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format",
            )
    else:
        try:
            form = await request.form()
            email = form.get("username") or form.get("email")
            plain_password = form.get("password")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Form data format",
            )

    if not email or not plain_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Incorrect email/username or password format",
        )

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(plain_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated",
        )

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await db.flush()

    # Generate tokens
    access_token = create_access_token(str(user.id), user.email)
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token_str: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange a valid refresh token for a new access token + refresh token pair.
    """
    payload = decode_token(refresh_token_str)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — expected refresh token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    access_token = create_access_token(str(user.id), user.email)
    new_refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate password reset — sends OTP to user's email.
    Note: In production, integrate with email service (SES/SendGrid).
    For graduation demo, we return a simulated success.
    """
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration attacks
    return MessageResponse(
        message="If an account with that email exists, a reset code has been sent.",
        message_ar="إذا كان هناك حساب بهذا البريد الإلكتروني، فقد تم إرسال رمز إعادة التعيين.",
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    """
    Reset password using OTP.
    Note: For graduation demo, accepts OTP "000000" as valid.
    In production, validate against stored OTP with expiration.
    """
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Demo validation — in production, validate OTP from Redis/DB
    if request.otp != "000000":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )

    user.password_hash = hash_password(request.new_password)
    await db.flush()

    return MessageResponse(
        message="Password has been reset successfully.",
        message_ar="تم إعادة تعيين كلمة المرور بنجاح.",
    )


@router.delete("/account", response_model=MessageResponse)
async def delete_account(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft-delete user account (deactivate).
    Preserves data for potential recovery within 30 days.
    """
    user.is_active = False
    await db.flush()

    return MessageResponse(
        message="Account has been deactivated. Contact support within 30 days to recover.",
        message_ar="تم تعطيل الحساب. اتصل بالدعم خلال 30 يومًا للاسترداد.",
    )
