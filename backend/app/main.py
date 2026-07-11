"""
PillScan API — Main Application Entry Point

FastAPI application with CORS, routers, lifecycle management, and OpenAPI docs.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import get_settings
from app.database import create_tables, ensure_new_columns
from app.routers import auth, users, drugs, scan, medications, reminders, adherence, leaflet

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.
    Runs on startup (before serving) and shutdown (after last request).
    """
    # ── Startup ──────────────────────────────────────────────────────
    print(f"[START] Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"   Environment: {settings.ENVIRONMENT}")

    # Create database tables. ``create_all`` is idempotent (it only creates
    # missing tables), so it is safe to run on every boot. This project ships
    # no Alembic migrations yet, so we rely on this in production too.
    await create_tables()
    await ensure_new_columns()  # add any columns introduced after initial schema
    print("   [SUCCESS] Database tables created/verified")

    # Auto-seed the default admin user + drug catalog. Idempotent, and crucial
    # on ephemeral hosts (Render free tier wipes the SQLite file each deploy).
    if settings.SEED_ON_STARTUP:
        try:
            from app.seed import seed_database
            await seed_database()
            print("   [SUCCESS] Database seed verified")
        except Exception as exc:  # never let seeding crash startup
            print(f"   [WARN] Seeding skipped due to error: {exc}")

    # Ensure upload directories exist
    os.makedirs("uploads/scans", exist_ok=True)
    print("   [SUCCESS] Upload directories ready")

    yield  # Application serves requests here

    # ── Shutdown ─────────────────────────────────────────────────────
    print(f"[SHUTDOWN] Shutting down {settings.APP_NAME}")


# ── Create FastAPI Application ───────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "PillScan API — AI-Powered Medication Identification & Management System.\n\n"
        "🏥 Identify medications from photos using deep learning\n"
        "💊 Manage medication schedules and reminders\n"
        "📊 Track medication adherence\n\n"
        "Built for the University of Tabuk CS Department Graduation Project (June 2026)."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ── CORS Middleware ──────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Static Files (Uploaded Images) ───────────────────────────────────────

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ── Register API Routers ─────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(drugs.router, prefix=API_PREFIX)
app.include_router(scan.router, prefix=API_PREFIX)
app.include_router(leaflet.router, prefix=API_PREFIX)
app.include_router(medications.router, prefix=API_PREFIX)
app.include_router(reminders.router, prefix=API_PREFIX)
app.include_router(adherence.router, prefix=API_PREFIX)


# ── Health Check ─────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check():
    """System health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["System"])
async def root():
    """Root endpoint — redirects to API documentation."""
    return {
        "message": "PillScan API",
        "message_ar": "واجهة برمجة تطبيقات بيل سكان",
        "docs": "/docs",
        "health": "/health",
    }
