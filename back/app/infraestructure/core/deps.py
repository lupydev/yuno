from typing import Annotated

from app.core.config import settings
from app.core.db import SessionDep
from app.models import User
from app.schemas import TokenPayload
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API}/auth/login")

TokenDep = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user(
    db: SessionDep,
    token: TokenDep,
) -> User:
    from app.services.user import get_user_by_id

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Las credenciales no son válidas",
        )
    user = await get_user_by_id(token_data.sub, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró este usuario en la base de datos.",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
