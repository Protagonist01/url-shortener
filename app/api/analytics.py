from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUserOptional, SessionDep
from app.schemas.analytics import URLAnalytics
from app.services import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/{short_code}", response_model=URLAnalytics)
async def get_analytics(
    short_code: str, db: SessionDep, user: CurrentUserOptional, days: int = 7
) -> URLAnalytics:
    result = await analytics_service.get_url_analytics(db, short_code, days=days)
    if result is None:
        raise HTTPException(status_code=404, detail="short url not found")
    return result
