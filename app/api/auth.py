from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.core.rate_limit import RateLimitAuth
from app.core.security import create_access_token
from app.models.models import User
from app.schemas.user import TokenResponse, UserCreate, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(payload: UserCreate, db: SessionDep, _: RateLimitAuth) -> User:
    existing = await auth_service.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email already registered",
        )
    return await auth_service.create_user(db, payload.email, payload.password)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserCreate, db: SessionDep, _: RateLimitAuth) -> TokenResponse:
    user = await auth_service.authenticate(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid credentials",
        )
    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token)
