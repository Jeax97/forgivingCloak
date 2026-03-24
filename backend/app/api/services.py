from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import (
    User, EmailAccount, DiscoveredService, ServiceStatus,
)
from app.schemas import DiscoveredServiceResponse, ServiceStatusUpdate
from app.api.deps import get_current_user

router = APIRouter(prefix="/services", tags=["services"])


@router.get("/", response_model=list[DiscoveredServiceResponse])
def list_discovered_services(
    email_account_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(DiscoveredService)
        .join(EmailAccount)
        .filter(EmailAccount.user_id == current_user.id)
    )
    if email_account_id:
        query = query.filter(DiscoveredService.email_account_id == email_account_id)
    if category:
        query = query.filter(DiscoveredService.category == category)
    if status_filter:
        query = query.filter(DiscoveredService.status == status_filter)
    if search:
        query = query.filter(DiscoveredService.service_name.ilike(f"%{search}%"))

    return query.order_by(DiscoveredService.detected_at.desc()).all()


@router.get("/{service_id}", response_model=DiscoveredServiceResponse)
def get_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = (
        db.query(DiscoveredService)
        .join(EmailAccount)
        .filter(DiscoveredService.id == service_id, EmailAccount.user_id == current_user.id)
        .first()
    )
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return service


@router.patch("/{service_id}/status", response_model=DiscoveredServiceResponse)
def update_service_status(
    service_id: int,
    data: ServiceStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = (
        db.query(DiscoveredService)
        .join(EmailAccount)
        .filter(DiscoveredService.id == service_id, EmailAccount.user_id == current_user.id)
        .first()
    )
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    try:
        service.status = ServiceStatus(data.status)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {data.status}")

    db.commit()
    db.refresh(service)
    return service


@router.get("/categories/list", response_model=list[str])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(DiscoveredService.category)
        .join(EmailAccount)
        .filter(EmailAccount.user_id == current_user.id)
        .distinct()
        .all()
    )
    return [r[0] for r in rows if r[0]]
