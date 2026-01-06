from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.db.database import get_db
from app.db import models
from app.schemas import token

# OAuth2 스킴 정의 (Token URL은 /api/v1/auth/login)
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

# 토큰 검증 및 사용자 조회 (Dependency)
async def get_current_user(
    token_str: str = Depends(reusable_oauth2),
    db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token_str, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        login_id: str = payload.get("sub")
        if login_id is None:
            raise credentials_exception
        token_data = token.TokenData(login_id=login_id)
    except (JWTError, ValidationError):
        raise credentials_exception
    
    # DB에서 사용자 조회 (AsyncSession)
    from sqlalchemy.future import select
    result = await db.execute(select(models.User).where(models.User.login_id == token_data.login_id))
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
    return user
