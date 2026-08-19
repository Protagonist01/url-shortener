from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import User
from app.services.auth_service import get_user_by_email

SessionDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user_optional(
    db: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
) -> User | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    email = decode_access_token(token)
    if email is None:
        return None
    return await get_user_by_email(db, email)


async def get_current_user(
    user: User | None = Depends(get_current_user_optional),
) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]
CurrentUser = Annotated[User, Depends(get_current_user)]
