from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import (
    User, EmailAccount, DiscoveredService, ScanJob, ServiceStatus, ScanStatus,
)
from app.schemas import DashboardStats, ScanJobResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base_query = (
        db.query(DiscoveredService)
        .join(EmailAccount)
        .filter(EmailAccount.user_id == current_user.id)
    )

    total = base_query.count()

    active = base_query.filter(
        DiscoveredService.status == ServiceStatus.ACTIVE
    ).count()

    deleted = base_query.filter(
        DiscoveredService.status == ServiceStatus.DELETED
    ).count()

    pending = base_query.filter(
        DiscoveredService.status.in_([
            ServiceStatus.DELETION_REQUESTED,
            ServiceStatus.DELETION_CONFIRMED,
        ])
    ).count()

    # Categories breakdown
    cat_rows = (
        base_query
        .with_entities(DiscoveredService.category, db.query(DiscoveredService).correlate(DiscoveredService).count())
    )
    # Simpler approach
    all_services = base_query.all()
    categories: dict[str, int] = {}
    for svc in all_services:
        cat = svc.category or "other"
        categories[cat] = categories.get(cat, 0) + 1

    recent_scans = (
        db.query(ScanJob)
        .join(EmailAccount)
        .filter(EmailAccount.user_id == current_user.id)
        .order_by(ScanJob.created_at.desc())
        .limit(5)
        .all()
    )

    return DashboardStats(
        total_accounts_found=total,
        active_accounts=active,
        deleted_accounts=deleted,
        pending_deletions=pending,
        categories=categories,
        recent_scans=recent_scans,
    )
