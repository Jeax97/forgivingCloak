from contextlib import asynccontextmanager

from sqlalchemy import inspect, text
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.api import (
    auth_router, scans_router, services_router,
    deletion_router, dashboard_router, settings_router,
)


def _run_migrations():
    """Add any missing columns to existing tables."""
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("scan_jobs")]
    if "status_message" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE scan_jobs ADD COLUMN status_message VARCHAR(500)"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _run_migrations()
    yield


app = FastAPI(
    title="Forgiving Cloak",
    description="Self-hosted email account discovery and deletion manager",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(scans_router, prefix="/api")
app.include_router(services_router, prefix="/api")
app.include_router(deletion_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(settings_router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}
