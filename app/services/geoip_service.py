"""GeoIP lookup service.

Resolves an IP address to a ISO 3166-1 alpha-2 country code.

Approach: uses ip-api.com's free JSON endpoint (no API key, no binary database
to manage, 45 requests/minute rate limit). For a demo project this is the right
tradeoff — zero setup, works immediately, and the lookup happens inside a Celery
task (off the request path), so the rate limit and latency don't affect redirects.

Production alternative: bundle a local MaxMind GeoLite2-Country.mmdb file and
use the `geoip2` library. That gives you:
  - No external API dependency (works offline, no rate limits)
  - Sub-millisecond lookups (memory-mapped binary search)
  - But: requires a free MaxMind account + license key to download the .mmdb,
    and you must refresh the file monthly (MaxMind updates GeoLite2 monthly).

We use the external API here for simplicity and zero-setup reproducibility.
The function signature is identical either way — swapping to geoip2 later
means changing only the body of `lookup_country`, not any callers.
"""
from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

IP_API_URL = "http://ip-api.com/json/{ip}?fields=countryCode"

# Private / loopback / link-local ranges can't be geo-located.
# In local development your IP is 127.0.0.1 or a Docker bridge address,
# so we short-circuit those to avoid wasting API calls.
PRIVATE_PREFIXES = ("127.", "192.168.", "10.", "172.16.", "::1", "localhost")


def lookup_country(ip_address: str | None) -> str | None:
    """Return a 2-letter country code (e.g. 'US', 'GB', 'DE') for the IP,
    or None if the IP is private, the API fails, or the lookup is inconclusive.

    Uses a synchronous `requests.get` because this function is called from
    a Celery task (synchronous context). If you ever call this from an async
    path, use httpx.AsyncClient instead.
    """
    if ip_address is None:
        return None

    if ip_address.startswith(PRIVATE_PREFIXES):
        return None

    try:
        response = requests.get(
            IP_API_URL.format(ip=ip_address),
            timeout=3,
        )
        response.raise_for_status()
        data = response.json()
        country = data.get("countryCode")
        if country and len(country) == 2:
            return country
        return None
    except Exception:
        # Don't let a GeoIP failure crash the click-recording task.
        # The click still gets recorded with country=None.
        logger.warning("GeoIP lookup failed for %s", ip_address, exc_info=True)
        return None
