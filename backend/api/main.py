"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.core.logging import setup_logging
from backend.api.middleware.auth import AuthMiddleware
from backend.api.routers import studies, datasets, sap, tlf, users, billing, help, ai_chat, knowledge

# SuperTokens ASGI middleware — handles /api/v1/auth/* routes
from supertokens_python.framework.fastapi import get_middleware

# 🔑 Initialize SuperTokens SDK (must run before app starts)
import backend.supertokens_init  # noqa: F401

logger = setup_logging(debug=settings.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Run database migrations asynchronously in the background
    # to avoid blocking GCP Cloud Run port 8080 startup check timeouts.
    import threading
    import time
    import random
    
    def db_upgrade():
        # Short random sleep prevents multi-worker setups from racing database locks
        time.sleep(random.random() * 1.5)
        try:
            logger.info("Background Auto-Migration: checking and upgrading database to head...")
            from alembic.config import Config
            from alembic import command
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            logger.info("Background Auto-Migration: upgrade completed successfully.")
        except Exception as err:
            logger.error(f"Background Auto-Migration failed: {err}", exc_info=True)
            
    threading.Thread(target=db_upgrade, daemon=True).start()
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# SuperTokens ASGI middleware — handles /api/v1/auth/* routes
app.add_middleware(get_middleware())

# Global middleware — order matters: auth runs before CORS headers are set
app.add_middleware(AuthMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(studies.router, prefix="/api/v1", tags=["studies"])
app.include_router(datasets.router, prefix="/api/v1", tags=["datasets"])
app.include_router(sap.router, prefix="/api/v1", tags=["sap"])
app.include_router(tlf.router, prefix="/api/v1", tags=["tlf"])
app.include_router(billing.router, prefix="/api/v1", tags=["billing"])
app.include_router(help.router, prefix="/api/v1")
app.include_router(ai_chat.router, prefix="/api/v1")
app.include_router(users.router)
app.include_router(knowledge.router, prefix="/api/v1", tags=["knowledge"])


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
