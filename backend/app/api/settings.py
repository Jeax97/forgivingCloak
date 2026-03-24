import json
from io import StringIO
import csv

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import encrypt_value
from app.models import User, EmailAccount, DiscoveredService, AppSettings
from app.schemas import SettingsUpdate
from app.api.deps import get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/")
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current app settings (sensitive values are masked)."""
    def _get(key: str) -> str | None:
        row = db.query(AppSettings).filter(AppSettings.key == key).first()
        return row.value if row else None

    hibp_key = _get("hibp_api_key")
    google_id = _get("google_client_id")

    return {
        "hibp_api_key_configured": bool(hibp_key),
        "google_oauth_configured": bool(google_id),
    }


@router.put("/")
def update_settings(
    data: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update app settings. Only admins can change settings."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    def _set(key: str, value: str | None):
        if value is None:
            return
        row = db.query(AppSettings).filter(AppSettings.key == key).first()
        encrypted = encrypt_value(value)
        if row:
            row.value = encrypted
        else:
            db.add(AppSettings(key=key, value=encrypted))

    _set("hibp_api_key", data.hibp_api_key)
    _set("google_client_id", data.google_client_id)
    _set("google_client_secret", data.google_client_secret)

    db.commit()
    return {"message": "Settings updated"}


@router.get("/export/json")
def export_data_json(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export all discovered services as JSON."""
    services = (
        db.query(DiscoveredService)
        .join(EmailAccount)
        .filter(EmailAccount.user_id == current_user.id)
        .all()
    )

    data = []
    for s in services:
        data.append({
            "service_name": s.service_name,
            "service_domain": s.service_domain,
            "category": s.category,
            "detection_method": s.detection_method.value if s.detection_method else None,
            "status": s.status.value if s.status else None,
            "detected_at": s.detected_at.isoformat() if s.detected_at else None,
            "deletion_url": s.deletion_url,
            "deletion_difficulty": s.deletion_difficulty,
        })

    return StreamingResponse(
        StringIO(json.dumps(data, indent=2)),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=forgivingcloak-export.json"},
    )


@router.get("/export/csv")
def export_data_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export all discovered services as CSV."""
    services = (
        db.query(DiscoveredService)
        .join(EmailAccount)
        .filter(EmailAccount.user_id == current_user.id)
        .all()
    )

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Service", "Domain", "Category", "Detection Method", "Status", "Detected At", "Deletion URL", "Difficulty"])

    for s in services:
        writer.writerow([
            s.service_name,
            s.service_domain,
            s.category,
            s.detection_method.value if s.detection_method else "",
            s.status.value if s.status else "",
            s.detected_at.isoformat() if s.detected_at else "",
            s.deletion_url or "",
            s.deletion_difficulty or "",
        ])

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=forgivingcloak-export.csv"},
    )
