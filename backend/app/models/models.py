from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


# --------------- Enums ---------------

class ScanType(str, enum.Enum):
    IMAP = "imap"
    HIBP = "hibp"
    PROBE = "probe"
    FULL = "full"


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ServiceStatus(str, enum.Enum):
    ACTIVE = "active"
    DELETION_REQUESTED = "deletion_requested"
    DELETION_CONFIRMED = "deletion_confirmed"
    DELETED = "deleted"
    IGNORED = "ignored"


class DeletionMethod(str, enum.Enum):
    DIRECT_LINK = "direct_link"
    GDPR_EMAIL = "gdpr_email"
    CCPA_EMAIL = "ccpa_email"
    MANUAL = "manual"


class DeletionStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    EMAIL_DRAFTED = "email_drafted"
    EMAIL_SENT = "email_sent"
    REQUESTED = "requested"
    CONFIRMED = "confirmed"


class EmailProvider(str, enum.Enum):
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    YAHOO = "yahoo"
    CUSTOM_IMAP = "custom_imap"


# --------------- Models ---------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    email_accounts = relationship("EmailAccount", back_populates="user", cascade="all, delete-orphan")


class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    email_address = Column(String(320), nullable=False)
    provider = Column(SAEnum(EmailProvider), nullable=False, default=EmailProvider.CUSTOM_IMAP)
    imap_host = Column(String(255), nullable=True)
    imap_port = Column(Integer, nullable=True, default=993)
    encrypted_password = Column(Text, nullable=True)
    # Gmail OAuth tokens (encrypted)
    encrypted_refresh_token = Column(Text, nullable=True)
    oauth_access_token = Column(Text, nullable=True)
    oauth_expiry = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    last_scanned = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User", back_populates="email_accounts")
    discovered_services = relationship("DiscoveredService", back_populates="email_account", cascade="all, delete-orphan")
    scan_jobs = relationship("ScanJob", back_populates="email_account", cascade="all, delete-orphan")


class DiscoveredService(Base):
    __tablename__ = "discovered_services"

    id = Column(Integer, primary_key=True, index=True)
    email_account_id = Column(Integer, ForeignKey("email_accounts.id", ondelete="CASCADE"), nullable=False)
    service_name = Column(String(200), nullable=False)
    service_domain = Column(String(255), nullable=True)
    service_icon = Column(String(500), nullable=True)
    category = Column(String(50), nullable=True)
    detection_method = Column(SAEnum(ScanType), nullable=False)
    status = Column(SAEnum(ServiceStatus), default=ServiceStatus.ACTIVE, nullable=False)
    detected_at = Column(DateTime, default=_utcnow)
    # Deletion info
    deletion_url = Column(String(500), nullable=True)
    deletion_difficulty = Column(Integer, nullable=True)  # 1-5
    deletion_notes = Column(Text, nullable=True)
    # Breach info (from HIBP)
    breach_date = Column(DateTime, nullable=True)
    breach_data_classes = Column(Text, nullable=True)  # JSON string

    email_account = relationship("EmailAccount", back_populates="discovered_services")
    deletion_requests = relationship("DeletionRequest", back_populates="discovered_service", cascade="all, delete-orphan")


class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id = Column(Integer, primary_key=True, index=True)
    email_account_id = Column(Integer, ForeignKey("email_accounts.id", ondelete="CASCADE"), nullable=False)
    scan_type = Column(SAEnum(ScanType), nullable=False)
    status = Column(SAEnum(ScanStatus), default=ScanStatus.PENDING, nullable=False)
    progress = Column(Integer, default=0)  # 0-100
    services_found = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    celery_task_id = Column(String(255), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    email_account = relationship("EmailAccount", back_populates="scan_jobs")


class DeletionRequest(Base):
    __tablename__ = "deletion_requests"

    id = Column(Integer, primary_key=True, index=True)
    discovered_service_id = Column(Integer, ForeignKey("discovered_services.id", ondelete="CASCADE"), nullable=False)
    method = Column(SAEnum(DeletionMethod), nullable=False)
    status = Column(SAEnum(DeletionStatus), default=DeletionStatus.NOT_STARTED, nullable=False)
    generated_email_subject = Column(String(500), nullable=True)
    generated_email_body = Column(Text, nullable=True)
    recipient_email = Column(String(320), nullable=True)
    notes = Column(Text, nullable=True)
    requested_at = Column(DateTime, default=_utcnow)
    confirmed_at = Column(DateTime, nullable=True)

    discovered_service = relationship("DiscoveredService", back_populates="deletion_requests")


class AppSettings(Base):
    """Key-value store for app-wide settings like setup_complete flag."""
    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
