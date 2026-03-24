from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import encrypt_value
from app.models import User, EmailAccount, ScanJob, ScanType, ScanStatus, EmailProvider
from app.schemas import (
    EmailAccountCreate, EmailAccountResponse, ScanRequest, ScanJobResponse,
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/scans", tags=["scans"])


# --------------- Email Accounts ---------------

@router.post("/email-accounts", response_model=EmailAccountResponse, status_code=status.HTTP_201_CREATED)
def add_email_account(
    data: EmailAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(EmailAccount).filter(
        EmailAccount.user_id == current_user.id,
        EmailAccount.email_address == data.email_address,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email account already added")

    account = EmailAccount(
        user_id=current_user.id,
        email_address=data.email_address,
        provider=EmailProvider(data.provider),
        imap_host=data.imap_host,
        imap_port=data.imap_port,
        encrypted_password=encrypt_value(data.password) if data.password else None,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/email-accounts", response_model=list[EmailAccountResponse])
def list_email_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(EmailAccount).filter(EmailAccount.user_id == current_user.id).all()


@router.delete("/email-accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_email_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = db.query(EmailAccount).filter(
        EmailAccount.id == account_id, EmailAccount.user_id == current_user.id
    ).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email account not found")
    db.delete(account)
    db.commit()


# --------------- Scan Jobs ---------------

@router.post("/start", response_model=list[ScanJobResponse])
def start_scan(
    data: ScanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = db.query(EmailAccount).filter(
        EmailAccount.id == data.email_account_id,
        EmailAccount.user_id == current_user.id,
    ).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email account not found")

    # Check for already running scans on this account
    running = db.query(ScanJob).filter(
        ScanJob.email_account_id == account.id,
        ScanJob.status.in_([ScanStatus.PENDING, ScanStatus.RUNNING]),
    ).first()
    if running:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A scan is already running for this account")

    created_jobs = []
    for scan_type_str in data.scan_types:
        try:
            scan_type = ScanType(scan_type_str)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid scan type: {scan_type_str}")

        job = ScanJob(
            email_account_id=account.id,
            scan_type=scan_type,
            status=ScanStatus.PENDING,
        )
        db.add(job)
        db.flush()
        created_jobs.append(job)

    db.commit()

    # Dispatch Celery tasks
    from app.tasks.scan_tasks import run_scan_job
    for job in created_jobs:
        task = run_scan_job.delay(job.id)
        job.celery_task_id = task.id
    db.commit()

    for job in created_jobs:
        db.refresh(job)
    return created_jobs


@router.get("/jobs", response_model=list[ScanJobResponse])
def list_scan_jobs(
    email_account_id: Optional[int] = Query(None),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(ScanJob)
        .join(EmailAccount)
        .filter(EmailAccount.user_id == current_user.id)
        .order_by(ScanJob.created_at.desc())
    )
    if email_account_id:
        query = query.filter(ScanJob.email_account_id == email_account_id)
    return query.limit(limit).all()


@router.get("/jobs/{job_id}", response_model=ScanJobResponse)
def get_scan_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = (
        db.query(ScanJob)
        .join(EmailAccount)
        .filter(ScanJob.id == job_id, EmailAccount.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan job not found")
    return job
