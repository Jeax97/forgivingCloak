"""Have I Been Pwned API client — checks email against known data breaches."""

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

HIBP_BASE_URL = "https://haveibeenpwned.com/api/v3"
_SERVICES_PATH = Path(__file__).parent.parent / "data" / "services.json"


@dataclass
class BreachResult:
    service_name: str
    service_domain: str
    breach_date: str | None = None
    data_classes: list[str] | None = None
    category: str | None = None
    deletion_url: str | None = None
    deletion_difficulty: int | None = None
    deletion_notes: str | None = None
    service_icon: str | None = None


def _load_service_registry() -> dict[str, dict]:
    if not _SERVICES_PATH.exists():
        return {}
    with open(_SERVICES_PATH, "r", encoding="utf-8") as f:
        services = json.load(f)
    return {s["domain"]: s for s in services if "domain" in s}


def check_breaches(
    email: str,
    api_key: str,
    progress_callback=None,
) -> list[BreachResult]:
    """Query HIBP API for breaches associated with the given email.

    Args:
        email: Email address to check
        api_key: HIBP API key (required for breachedaccount endpoint)
        progress_callback: Optional callable(progress: int) for progress updates

    Returns:
        List of breach results
    """
    registry = _load_service_registry()
    results: list[BreachResult] = []

    headers = {
        "hibp-api-key": api_key,
        "user-agent": "ForgivingCloak/1.0",
    }

    if progress_callback:
        progress_callback(10, "Querying breach database…")

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(
                f"{HIBP_BASE_URL}/breachedaccount/{email}",
                headers=headers,
                params={"truncateResponse": "false"},
            )

            if resp.status_code == 404:
                logger.info("No breaches found for %s", email)
                if progress_callback:
                    progress_callback(100, "No breaches found")
                return []

            if resp.status_code == 401:
                raise ValueError("Invalid HIBP API key")

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("retry-after", "5"))
                logger.warning("HIBP rate limited, waiting %ds", retry_after)
                time.sleep(retry_after)
                resp = client.get(
                    f"{HIBP_BASE_URL}/breachedaccount/{email}",
                    headers=headers,
                    params={"truncateResponse": "false"},
                )

            resp.raise_for_status()
            breaches = resp.json()

    except httpx.HTTPStatusError as e:
        logger.error("HIBP API error: %s", e)
        raise
    except httpx.RequestError as e:
        logger.error("HIBP connection error: %s", e)
        raise

    total = len(breaches)
    for i, breach in enumerate(breaches):
        domain = breach.get("Domain", "").lower()
        name = breach.get("Name", breach.get("Title", "Unknown"))

        # Enrich from service registry
        svc = registry.get(domain, {})

        result = BreachResult(
            service_name=svc.get("name", name),
            service_domain=domain or name.lower().replace(" ", ""),
            breach_date=breach.get("BreachDate"),
            data_classes=breach.get("DataClasses"),
            category=svc.get("category"),
            deletion_url=svc.get("deletion_url"),
            deletion_difficulty=svc.get("deletion_difficulty"),
            deletion_notes=svc.get("deletion_notes"),
            service_icon=svc.get("icon"),
        )
        results.append(result)

        if progress_callback:
            progress_callback(min(10 + int(i / total * 90), 99), f"Checking breach {i + 1}/{total}…")

    if progress_callback:
        progress_callback(100, f"{len(results)} breaches found")

    return results
