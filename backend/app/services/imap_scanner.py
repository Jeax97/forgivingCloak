"""IMAP email scanner — detects signup confirmation emails to discover registered services."""

import json
import logging
import re
import time
from dataclasses import dataclass
from email.utils import parseaddr
from pathlib import Path

from imap_tools import MailBox, AND, MailMessage

from app.core.config import settings
from app.core.security import decrypt_value

logger = logging.getLogger(__name__)

# Load service registry
_SERVICES_PATH = Path(__file__).parent.parent / "data" / "services.json"

SUBJECT_PATTERNS = [
    re.compile(r"(?i)welcome\s+to\s+(.+)"),
    re.compile(r"(?i)confirm\s+your\s+(.+?)\s*(email|account|registration)"),
    re.compile(r"(?i)verify\s+your\s+(.+?)\s*(email|account)"),
    re.compile(r"(?i)thanks?\s+for\s+(signing up|registering|joining)\s*(with|to|for)?\s*(.+)?"),
    re.compile(r"(?i)your\s+(.+?)\s+account\s+(has been|is)\s+(created|ready)"),
    re.compile(r"(?i)activate\s+your\s+(.+?)\s*account"),
    re.compile(r"(?i)complete\s+your\s+(.+?)\s*registration"),
]

SENDER_KEYWORDS = [
    "noreply", "no-reply", "verify", "registration", "confirm",
    "welcome", "signup", "sign-up", "accounts", "notifications",
]


@dataclass
class DetectedService:
    service_name: str
    service_domain: str
    category: str | None = None
    deletion_url: str | None = None
    deletion_difficulty: int | None = None
    deletion_notes: str | None = None
    service_icon: str | None = None


def _load_service_registry() -> dict[str, dict]:
    """Load services.json and index by domain."""
    if not _SERVICES_PATH.exists():
        return {}
    with open(_SERVICES_PATH, "r", encoding="utf-8") as f:
        services = json.load(f)
    return {s["domain"]: s for s in services if "domain" in s}


def _extract_domain(email_address: str) -> str:
    """Extract domain from email address."""
    _, addr = parseaddr(email_address)
    if "@" in addr:
        return addr.split("@")[1].lower()
    return email_address.lower()


def _match_service(sender_domain: str, subject: str, registry: dict[str, dict]) -> DetectedService | None:
    """Try to match sender domain and subject against the service registry."""
    # Direct domain match
    if sender_domain in registry:
        svc = registry[sender_domain]
        return DetectedService(
            service_name=svc["name"],
            service_domain=sender_domain,
            category=svc.get("category"),
            deletion_url=svc.get("deletion_url"),
            deletion_difficulty=svc.get("deletion_difficulty"),
            deletion_notes=svc.get("deletion_notes"),
            service_icon=svc.get("icon"),
        )

    # Check if sender domain is a subdomain of a known service
    parts = sender_domain.split(".")
    for i in range(len(parts) - 1):
        parent = ".".join(parts[i:])
        if parent in registry:
            svc = registry[parent]
            return DetectedService(
                service_name=svc["name"],
                service_domain=parent,
                category=svc.get("category"),
                deletion_url=svc.get("deletion_url"),
                deletion_difficulty=svc.get("deletion_difficulty"),
                deletion_notes=svc.get("deletion_notes"),
                service_icon=svc.get("icon"),
            )

    # Try pattern matching on subject
    for pattern in SUBJECT_PATTERNS:
        match = pattern.search(subject)
        if match:
            possible_name = match.group(1).strip().rstrip("!.").strip()
            if possible_name and len(possible_name) < 60:
                return DetectedService(
                    service_name=possible_name,
                    service_domain=sender_domain,
                )

    return None


def _is_signup_email(msg: MailMessage) -> bool:
    """Heuristic check whether an email looks like a signup confirmation."""
    subject = (msg.subject or "").lower()
    signup_subject_words = [
        "welcome", "confirm", "verify", "activate", "registration",
        "sign up", "signed up", "account created", "get started",
    ]
    if any(w in subject for w in signup_subject_words):
        return True

    sender_local = (msg.from_ or "").split("@")[0].lower()
    if any(kw in sender_local for kw in SENDER_KEYWORDS):
        return True

    return False


def scan_imap(
    host: str,
    port: int,
    email_address: str,
    encrypted_password: str,
    progress_callback=None,
) -> list[DetectedService]:
    """Scan an IMAP mailbox for signup confirmation emails.

    Args:
        host: IMAP server hostname
        port: IMAP server port (usually 993)
        email_address: User's email address (used as login)
        encrypted_password: Fernet-encrypted password
        progress_callback: Optional callable(progress: int) for 0-100 progress updates

    Returns:
        List of detected services
    """
    password = decrypt_value(encrypted_password)
    registry = _load_service_registry()
    detected: dict[str, DetectedService] = {}

    with MailBox(host, port).login(email_address, password) as mailbox:
        # Fetch all mail UIDs to calculate progress
        all_uids = [msg.uid for msg in mailbox.fetch(AND(all=True), headers_only=True, mark_seen=False)]
        total = min(len(all_uids), settings.IMAP_MAX_EMAILS) if settings.IMAP_MAX_EMAILS else len(all_uids)

        if total == 0:
            if progress_callback:
                progress_callback(100)
            return []

        processed = 0
        for msg in mailbox.fetch(AND(all=True), mark_seen=False, bulk=50):
            if settings.IMAP_MAX_EMAILS and processed >= settings.IMAP_MAX_EMAILS:
                break

            processed += 1
            if progress_callback and processed % 20 == 0:
                progress_callback(min(int(processed / total * 100), 99))

            if not _is_signup_email(msg):
                continue

            sender_domain = _extract_domain(msg.from_ or "")
            subject = msg.subject or ""

            service = _match_service(sender_domain, subject, registry)
            if service and service.service_domain not in detected:
                detected[service.service_domain] = service

            if settings.IMAP_FETCH_DELAY:
                time.sleep(settings.IMAP_FETCH_DELAY)

    if progress_callback:
        progress_callback(100)

    return list(detected.values())


def scan_imap_oauth(
    email_address: str,
    access_token: str,
    progress_callback=None,
) -> list[DetectedService]:
    """Scan Gmail via OAuth XOAUTH2 authentication."""
    import imaplib
    import base64

    registry = _load_service_registry()
    detected: dict[str, DetectedService] = {}

    # Build XOAUTH2 string
    auth_string = f"user={email_address}\x01auth=Bearer {access_token}\x01\x01"
    auth_bytes = base64.b64encode(auth_string.encode()).decode()

    imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    imap.authenticate("XOAUTH2", lambda _: auth_bytes.encode())
    imap.select("INBOX", readonly=True)

    # Search for potential signup emails
    search_queries = [
        '(SUBJECT "welcome to")',
        '(SUBJECT "confirm your")',
        '(SUBJECT "verify your")',
        '(SUBJECT "account created")',
        '(SUBJECT "sign up")',
        '(SUBJECT "registration")',
    ]

    all_uids: set[bytes] = set()
    for query in search_queries:
        _, data = imap.search(None, query)
        if data[0]:
            all_uids.update(data[0].split())

    total = len(all_uids)
    processed = 0

    for uid in all_uids:
        if settings.IMAP_MAX_EMAILS and processed >= settings.IMAP_MAX_EMAILS:
            break

        processed += 1
        if progress_callback and processed % 10 == 0:
            progress_callback(min(int(processed / total * 100), 99))

        _, msg_data = imap.fetch(uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])")
        if not msg_data or not msg_data[0]:
            continue

        raw = msg_data[0][1] if isinstance(msg_data[0], tuple) else b""
        header_text = raw.decode("utf-8", errors="replace")

        from_match = re.search(r"From:\s*(.+)", header_text, re.IGNORECASE)
        subject_match = re.search(r"Subject:\s*(.+)", header_text, re.IGNORECASE)

        sender = from_match.group(1).strip() if from_match else ""
        subject = subject_match.group(1).strip() if subject_match else ""

        sender_domain = _extract_domain(sender)
        service = _match_service(sender_domain, subject, registry)
        if service and service.service_domain not in detected:
            detected[service.service_domain] = service

        if settings.IMAP_FETCH_DELAY:
            time.sleep(settings.IMAP_FETCH_DELAY)

    imap.close()
    imap.logout()

    if progress_callback:
        progress_callback(100)

    return list(detected.values())
