from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import (
    User, EmailAccount, DiscoveredService, DeletionRequest,
    DeletionMethod, DeletionStatus, ServiceStatus,
)
from app.schemas import (
    DeletionRequestCreate, DeletionRequestResponse, DeletionStatusUpdate,
)
from app.services.email_generator import generate_deletion_email
from app.api.deps import get_current_user

router = APIRouter(prefix="/deletion", tags=["deletion"])


@router.post("/request", response_model=DeletionRequestResponse, status_code=status.HTTP_201_CREATED)
def create_deletion_request(
    data: DeletionRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = (
        db.query(DiscoveredService)
        .join(EmailAccount)
        .filter(
            DiscoveredService.id == data.discovered_service_id,
            EmailAccount.user_id == current_user.id,
        )
        .first()
    )
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    try:
        method = DeletionMethod(data.method)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid method: {data.method}")

    deletion = DeletionRequest(
        discovered_service_id=service.id,
        method=method,
    )

    # Generate email content for email-based methods
    if method in (DeletionMethod.GDPR_EMAIL, DeletionMethod.CCPA_EMAIL):
        email_data = generate_deletion_email(
            user_name=current_user.full_name or current_user.username,
            user_email=service.email_account.email_address,
            service_name=service.service_name,
            service_domain=service.service_domain,
            regulation="gdpr" if method == DeletionMethod.GDPR_EMAIL else "ccpa",
        )
        deletion.generated_email_subject = email_data["subject"]
        deletion.generated_email_body = email_data["body"]
        deletion.recipient_email = email_data["recipient"]
        deletion.status = DeletionStatus.EMAIL_DRAFTED

    # Update service status
    service.status = ServiceStatus.DELETION_REQUESTED

    db.add(deletion)
    db.commit()
    db.refresh(deletion)
    return deletion


@router.get("/requests", response_model=list[DeletionRequestResponse])
def list_deletion_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(DeletionRequest)
        .join(DiscoveredService)
        .join(EmailAccount)
        .filter(EmailAccount.user_id == current_user.id)
        .order_by(DeletionRequest.requested_at.desc())
        .all()
    )


@router.patch("/{request_id}/status", response_model=DeletionRequestResponse)
def update_deletion_status(
    request_id: int,
    data: DeletionStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deletion = (
        db.query(DeletionRequest)
        .join(DiscoveredService)
        .join(EmailAccount)
        .filter(DeletionRequest.id == request_id, EmailAccount.user_id == current_user.id)
        .first()
    )
    if not deletion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deletion request not found")

    try:
        deletion.status = DeletionStatus(data.status)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {data.status}")

    if data.notes:
        deletion.notes = data.notes

    if deletion.status == DeletionStatus.CONFIRMED:
        deletion.confirmed_at = datetime.now(timezone.utc)
        deletion.discovered_service.status = ServiceStatus.DELETED

    db.commit()
    db.refresh(deletion)
    return deletion
