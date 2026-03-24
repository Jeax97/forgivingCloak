"""Gmail OAuth 2.0 helper — handles authorization flow and token refresh."""

import logging

import httpx

from app.core.config import settings
from app.core.security import encrypt_value, decrypt_value

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPES = ["https://mail.google.com/"]


def get_authorization_url(state: str | None = None) -> str:
    """Build the Google OAuth authorization URL for the user to visit."""
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    if state:
        params["state"] = state

    query = "&".join(f"{k}={httpx.URL('', params={k: v}).params[k]}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{query}"


def exchange_code_for_tokens(code: str) -> dict:
    """Exchange the authorization code for access and refresh tokens.

    Returns:
        Dict with keys: access_token, refresh_token, expires_in, email
    """
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        token_data = resp.json()

        # Get user's email
        userinfo_resp = client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        userinfo_resp.raise_for_status()
        email = userinfo_resp.json().get("email", "")

    return {
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token"),
        "expires_in": token_data.get("expires_in", 3600),
        "email": email,
    }


def refresh_access_token(encrypted_refresh_token: str) -> dict:
    """Refresh an expired access token using the stored refresh token.

    Returns:
        Dict with keys: access_token, expires_in
    """
    refresh_token = decrypt_value(encrypted_refresh_token)

    with httpx.Client(timeout=30) as client:
        resp = client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        resp.raise_for_status()
        token_data = resp.json()

    return {
        "access_token": token_data["access_token"],
        "expires_in": token_data.get("expires_in", 3600),
    }
