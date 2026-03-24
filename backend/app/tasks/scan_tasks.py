"""Celery tasks for background scanning operations."""

import json
import logging
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.security import decrypt_value
from app.models import (
    EmailAccount, ScanJob, DiscoveredService,
    ScanType, ScanStatus, ServiceStatus, EmailProvider, AppSettings,
)

logger = logging.getLogger(__name__)


def _update_job(db, job: ScanJob, **kwargs):
    for k, v in kwargs.items():
        setattr(job, k, v)
    db.commit()


def _add_discovered_service(db, email_account_id: int, service_data: dict, method: ScanType):
    """Add a discovered service if not already tracked for this email account."""
    existing = db.query(DiscoveredService).filter(
        DiscoveredService.email_account_id == email_account_id,
        DiscoveredService.service_domain == service_data.get("service_domain"),
    ).first()

    if existing:
        return False

    svc = DiscoveredService(
        email_account_id=email_account_id,
        service_name=service_data["service_name"],
        service_domain=service_data.get("service_domain"),
        service_icon=service_data.get("service_icon"),
        category=service_data.get("category"),
        detection_method=method,
        status=ServiceStatus.ACTIVE,
        deletion_url=service_data.get("deletion_url"),
        deletion_difficulty=service_data.get("deletion_difficulty"),
        deletion_notes=service_data.get("deletion_notes"),
        breach_date=(
            datetime.fromisoformat(service_data["breach_date"])
            if service_data.get("breach_date")
            else None
        ),
        breach_data_classes=(
            json.dumps(service_data["data_classes"])
            if service_data.get("data_classes")
            else None
        ),
    )
    db.add(svc)
    db.commit()
    return True


@celery_app.task(bind=True, name="run_scan_job")
def run_scan_job(self, job_id: int):
    """Execute a scan job based on its type."""
    db = SessionLocal()
    try:
        job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
        if not job:
            logger.error("Scan job %d not found", job_id)
            return

        account = db.query(EmailAccount).filter(EmailAccount.id == job.email_account_id).first()
        if not account:
            _update_job(db, job, status=ScanStatus.FAILED, error_message="Email account not found")
            return

        _update_job(
            db, job,
            status=ScanStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            celery_task_id=self.request.id,
        )

        def progress_callback(progress: int):
            _update_job(db, job, progress=progress)

        try:
            if job.scan_type == ScanType.IMAP:
                results = _run_imap_scan(account, progress_callback)
            elif job.scan_type == ScanType.HIBP:
                results = _run_hibp_scan(db, account, progress_callback)
            elif job.scan_type == ScanType.PROBE:
                results = _run_probe_scan(account, progress_callback)
            else:
                results = []

            # Store results
            new_count = 0
            for result in results:
                added = _add_discovered_service(
                    db, account.id, result.__dict__, job.scan_type
                )
                if added:
                    new_count += 1

            account.last_scanned = datetime.now(timezone.utc)
            _update_job(
                db, job,
                status=ScanStatus.COMPLETED,
                progress=100,
                services_found=new_count,
                completed_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.exception("Scan job %d failed: %s", job_id, e)
            _update_job(
                db, job,
                status=ScanStatus.FAILED,
                error_message=str(e),
                completed_at=datetime.now(timezone.utc),
            )

    finally:
        db.close()


def _run_imap_scan(account: EmailAccount, progress_callback):
    """Run IMAP-based email scanning."""
    if account.provider == EmailProvider.GMAIL and account.encrypted_refresh_token:
        from app.services.gmail_oauth import refresh_access_token
        tokens = refresh_access_token(account.encrypted_refresh_token)

        from app.services.imap_scanner import scan_imap_oauth
        return scan_imap_oauth(
            email_address=account.email_address,
            access_token=tokens["access_token"],
            progress_callback=progress_callback,
        )
    elif account.encrypted_password:
        from app.services.imap_scanner import scan_imap
        return scan_imap(
            host=account.imap_host or "imap.gmail.com",
            port=account.imap_port or 993,
            email_address=account.email_address,
            encrypted_password=account.encrypted_password,
            progress_callback=progress_callback,
        )
    else:
        raise ValueError("No credentials configured for this email account")


def _run_hibp_scan(db, account: EmailAccount, progress_callback):
    """Run Have I Been Pwned breach check."""
    # Get HIBP API key from app settings
    setting = db.query(AppSettings).filter(AppSettings.key == "hibp_api_key").first()
    if not setting or not setting.value:
        raise ValueError("HIBP API key not configured. Add it in Settings.")

    api_key = decrypt_value(setting.value)

    from app.services.hibp_client import check_breaches
    return check_breaches(
        email=account.email_address,
        api_key=api_key,
        progress_callback=progress_callback,
    )


def _run_probe_scan(account: EmailAccount, progress_callback):
    """Run direct website probing."""
    from app.services.site_prober import probe_services
    return probe_services(
        email=account.email_address,
        progress_callback=progress_callback,
    )
