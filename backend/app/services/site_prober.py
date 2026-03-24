"""Direct website prober — checks if an email is registered on specific services."""

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_SERVICES_PATH = Path(__file__).parent.parent / "data" / "services.json"

CLOUDFLARE_SIGNATURES = [
    "cf-ray",
    "cloudflare",
    "attention required",
    "checking your browser",
]


@dataclass
class ProbeResult:
    service_name: str
    service_domain: str
    is_registered: bool
    category: str | None = None
    deletion_url: str | None = None
    deletion_difficulty: int | None = None
    deletion_notes: str | None = None
    service_icon: str | None = None


def _load_probeable_services() -> list[dict]:
    """Load services that have probe configurations defined."""
    if not _SERVICES_PATH.exists():
        return []
    with open(_SERVICES_PATH, "r", encoding="utf-8") as f:
        services = json.load(f)
    return [s for s in services if s.get("probe")]


def _is_waf_blocked(response: httpx.Response) -> bool:
    """Detect if the response is from a WAF (Cloudflare, etc.)."""
    headers_str = str(response.headers).lower()
    body_lower = response.text.lower()[:2000]
    return any(sig in headers_str or sig in body_lower for sig in CLOUDFLARE_SIGNATURES)


async def _probe_service(
    client: httpx.AsyncClient,
    service: dict,
    email: str,
) -> ProbeResult | None:
    """Probe a single service to check if the email is registered."""
    probe_config = service["probe"]
    method = probe_config.get("method", "POST")
    url = probe_config["url"]
    detection = probe_config.get("detection", "message")

    try:
        if method.upper() == "POST":
            payload = {}
            field_name = probe_config.get("email_field", "email")
            payload[field_name] = email

            content_type = probe_config.get("content_type", "json")
            if content_type == "json":
                resp = await client.post(url, json=payload, timeout=15)
            else:
                resp = await client.post(url, data=payload, timeout=15)
        else:
            formatted_url = url.replace("{email}", email)
            resp = await client.get(formatted_url, timeout=15)

        if _is_waf_blocked(resp):
            logger.debug("WAF blocked probe for %s", service["name"])
            return None

        is_registered = False

        if detection == "status_code":
            expected = probe_config.get("registered_status", 200)
            is_registered = resp.status_code == expected

        elif detection == "message":
            body = resp.text.lower()
            registered_patterns = probe_config.get("registered_patterns", [])
            not_registered_patterns = probe_config.get("not_registered_patterns", [])

            if not_registered_patterns:
                not_found = any(p.lower() in body for p in not_registered_patterns)
                is_registered = not not_found
            elif registered_patterns:
                is_registered = any(p.lower() in body for p in registered_patterns)

        elif detection == "json_field":
            try:
                data = resp.json()
                field = probe_config.get("field", "exists")
                is_registered = bool(data.get(field))
            except (ValueError, KeyError):
                return None

        if is_registered:
            return ProbeResult(
                service_name=service["name"],
                service_domain=service["domain"],
                is_registered=True,
                category=service.get("category"),
                deletion_url=service.get("deletion_url"),
                deletion_difficulty=service.get("deletion_difficulty"),
                deletion_notes=service.get("deletion_notes"),
                service_icon=service.get("icon"),
            )

    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.debug("Probe failed for %s: %s", service["name"], e)
    except Exception as e:
        logger.debug("Unexpected error probing %s: %s", service["name"], e)

    return None


async def _probe_batch(
    services: list[dict],
    email: str,
    progress_callback=None,
) -> list[ProbeResult]:
    """Probe a batch of services concurrently with bounded concurrency."""
    results: list[ProbeResult] = []
    semaphore = asyncio.Semaphore(settings.MAX_PROBE_CONCURRENCY)
    total = len(services)

    async def _limited_probe(client: httpx.AsyncClient, svc: dict, idx: int):
        async with semaphore:
            result = await _probe_service(client, svc, email)
            if result:
                results.append(result)
            if progress_callback and idx % 5 == 0:
                progress_callback(min(int(idx / total * 100), 99), f"Probing service {idx + 1}/{total}…")

    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (compatible; ForgivingCloak/1.0)"},
        follow_redirects=True,
    ) as client:
        tasks = [_limited_probe(client, svc, i) for i, svc in enumerate(services)]
        await asyncio.gather(*tasks, return_exceptions=True)

    if progress_callback:
        progress_callback(100, f"{len(results)} services detected via probing")

    return results


def probe_services(
    email: str,
    progress_callback=None,
) -> list[ProbeResult]:
    """Synchronous wrapper to probe all configured services for an email.

    This method is opt-in and should only be used with explicit user consent.
    It checks forgot-password and registration endpoints which may trigger
    emails or rate limiting on the target services.
    """
    services = _load_probeable_services()
    if not services:
        if progress_callback:
            progress_callback(100, "No probeable services configured")
        return []

    return asyncio.run(_probe_batch(services, email, progress_callback))
