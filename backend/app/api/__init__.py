from app.api.auth import router as auth_router
from app.api.scans import router as scans_router
from app.api.services import router as services_router
from app.api.deletion import router as deletion_router
from app.api.dashboard import router as dashboard_router
from app.api.settings import router as settings_router

__all__ = [
    "auth_router",
    "scans_router",
    "services_router",
    "deletion_router",
    "dashboard_router",
    "settings_router",
]
