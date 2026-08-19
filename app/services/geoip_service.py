"""GeoIP lookup service.

Resolves an IP address to a ISO 3166-1 alpha-2 country code.

Two entry points:
  - `lookup_country(ip)` — sync, for the Celery worker path
  - `lookup_country_async(ip)` — async, for the BackgroundTasks path

Both call ip-api.com's free JSON endpoint (no API key, 45 req/min rate
limit). The sync version uses httpx.Client, the async version uses
httpx.AsyncClient. We use httpx (already a dependency for tests) instead
of requests so we don't add a dependency just for one HTTP call.

Production alternative: bundle a local MaxMind GeoLite2-Country.mmdb
file and use the `geoip2` library. That gives sub-millisecond lookups
with no external API dependency, but requires a free MaxMind account
and a monthly database refresh. The function signature is identical
either way — swapping means changing only the body.
"""
from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

IP_API_URL = "http://ip-api.com/json/{ip}?fields=countryCode"

# Private / loopback / link-local ranges can't be geo-located.
PRIVATE_PREFIXES = ("127.", "192.168.", "10.", "172.16.", "::1", "localhost")


def lookup_country(ip_address: str | None) -> str | None:
    """Sync lookup — called from the Celery worker task."""
    if ip_address is None or ip_address.startswith(PRIVATE_PREFIXES):
        return None
    try:
        response = httpx.get(IP_API_URL.format(ip=ip_address), timeout=3)
        response.raise_for_status()
        data = response.json()
        country = data.get("countryCode")
        return country if country and len(country) == 2 else None
    except Exception:
        logger.warning("GeoIP lookup failed for %s", ip_address, exc_info=True)
        return None


async def lookup_country_async(ip_address: str | None) -> str | None:
    """Async lookup — called from the BackgroundTasks click recorder."""
    if ip_address is None or ip_address.startswith(PRIVATE_PREFIXES):
        return None
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(IP_API_URL.format(ip=ip_address))
            response.raise_for_status()
            data = response.json()
            country = data.get("countryCode")
            return country if country and len(country) == 2 else None
    except Exception:
        logger.warning("GeoIP lookup failed for %s", ip_address, exc_info=True)
        return None
