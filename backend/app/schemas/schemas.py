from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# --------------- Auth ---------------

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --------------- Email Account ---------------

class EmailAccountCreate(BaseModel):
    email_address: EmailStr
    provider: str = "custom_imap"
    imap_host: Optional[str] = None
    imap_port: int = 993
    password: Optional[str] = None  # Will be encrypted


class EmailAccountResponse(BaseModel):
    id: int
    email_address: str
    provider: str
    imap_host: Optional[str]
    imap_port: Optional[int]
    is_active: bool
    last_scanned: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# --------------- Scan ---------------

class ScanRequest(BaseModel):
    email_account_id: int
    scan_types: list[str]  # ["imap", "hibp", "probe"]


class ScanJobResponse(BaseModel):
    id: int
    email_account_id: int
    scan_type: str
    status: str
    progress: int
    services_found: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# --------------- Discovered Service ---------------

class DiscoveredServiceResponse(BaseModel):
    id: int
    email_account_id: int
    service_name: str
    service_domain: Optional[str]
    service_icon: Optional[str]
    category: Optional[str]
    detection_method: str
    status: str
    detected_at: datetime
    deletion_url: Optional[str]
    deletion_difficulty: Optional[int]
    deletion_notes: Optional[str]
    breach_date: Optional[datetime]

    model_config = {"from_attributes": True}


class ServiceStatusUpdate(BaseModel):
    status: str


# --------------- Deletion ---------------

class DeletionRequestCreate(BaseModel):
    discovered_service_id: int
    method: str  # "direct_link", "gdpr_email", "ccpa_email", "manual"


class DeletionRequestResponse(BaseModel):
    id: int
    discovered_service_id: int
    method: str
    status: str
    generated_email_subject: Optional[str]
    generated_email_body: Optional[str]
    recipient_email: Optional[str]
    notes: Optional[str]
    requested_at: datetime
    confirmed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class DeletionStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


# --------------- Dashboard ---------------

class DashboardStats(BaseModel):
    total_accounts_found: int
    active_accounts: int
    deleted_accounts: int
    pending_deletions: int
    categories: dict[str, int]
    recent_scans: list[ScanJobResponse]


# --------------- Settings ---------------

class SettingsUpdate(BaseModel):
    hibp_api_key: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None


class SetupCheck(BaseModel):
    is_setup_complete: bool
    has_admin_user: bool
