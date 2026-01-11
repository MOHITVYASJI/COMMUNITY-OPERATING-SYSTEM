"""Authentication utilities - Mock OTP and JWT"""
import os
import jwt
import random
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_redis_client, get_db
from models import User
from sqlalchemy.orm import Session

JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
OTP_EXPIRY = int(os.getenv('OTP_EXPIRY_SECONDS', 300))  # 5 minutes

security = HTTPBearer()

def generate_otp(phone: str) -> str:
    """Generate and store OTP in Redis (Mock: always returns 123456)"""
    otp = "123456"  # Mock OTP for development
    redis_client = get_redis_client()
    
    # Store OTP in Redis with expiry
    redis_key = f"otp:{phone}"
    redis_client.setex(redis_key, OTP_EXPIRY, otp)
    
    print(f"✓ Mock OTP for {phone}: {otp} (valid for {OTP_EXPIRY}s)")
    return otp

def verify_otp(phone: str, otp: str) -> bool:
    """Verify OTP from Redis"""
    redis_client = get_redis_client()
    redis_key = f"otp:{phone}"
    
    stored_otp = redis_client.get(redis_key)
    
    if not stored_otp:
        return False
    
    # OTP matches
    if stored_otp == otp:
        # Delete OTP after successful verification
        redis_client.delete(redis_key)
        return True
    
    return False

def create_access_token(user_id: int, phone: str, role: str) -> str:
    """Create JWT access token"""
    payload = {
        "user_id": user_id,
        "phone": phone,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=7)  # 7 days expiry
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def decode_token(token: str) -> dict:
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = decode_token(token)
    
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

def require_role(allowed_roles: list):
    """Dependency to check user role"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}"
            )
        return current_user
    return role_checker
