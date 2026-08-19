import re

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.api.deps import CurrentUserOptional, SessionDep
from app.core.metrics import clicks_enqueued_total
from app.core.rate_limit import RateLimitRedirect
from app.services import url_service
from app.services.click_service import track_click

router = APIRouter(tags=["redirect"])

CODE_RE = re.compile(r"^[0-9A-Za-z]{1,16}$")


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.get("/{short_code}", response_class=RedirectResponse)
async def redirect(
    short_code: str,
    request: Request,
    db: SessionDep,
    user: CurrentUserOptional,
    background_tasks: BackgroundTasks,
    _: RateLimitRedirect,
) -> RedirectResponse:
    if not CODE_RE.match(short_code):
        raise HTTPException(status_code=404, detail="not found")

    target = await url_service.resolve_short_url(db, short_code)
    if target is None:
        raise HTTPException(status_code=404, detail="short url not found")

    # Dispatch to Celery or BackgroundTasks depending on config.
    # Either way, the 302 returns immediately — click persistence
    # happens after the response is sent.
    track_click(
        background_tasks=background_tasks,
        url_id=target["id"],
        short_code=target["short_code"],
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        referer=request.headers.get("referer"),
    )
    clicks_enqueued_total.inc()

    return RedirectResponse(url=target["original_url"], status_code=302)
