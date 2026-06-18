"""Authentication middleware for FastAPI.

Verifies SuperTokens session tokens from incoming requests,
injects tenant context into request state, and auto-provisions
Tenant/User records in the application database on first login.

Replaced the old Stack-Auth JWT verification.
"""
from typing import Callable
from uuid import UUID
from datetime import datetime

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select

from backend.core.security import verify_supertokens_session, TokenData
from backend.db.session import async_session_factory
from backend.db.models import Tenant, User


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware that validates SuperTokens session and sets tenant context."""

    # Paths that don't require authentication
    PUBLIC_PATHS = {
        "/api/v1/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip auth for public paths and SuperTokens auth endpoints
        if request.url.path in self.PUBLIC_PATHS or request.url.path.startswith("/api/v1/auth/"):
            return await call_next(request)

        # Extract token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        token = auth_header.removeprefix("Bearer ")

        # Verify with SuperTokens
        token_data = await verify_supertokens_session(request, token)
        if token_data is None:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        # Set tenant context on request state
        request.state.user_id = token_data.user_id
        request.state.tenant_id = token_data.team_id
        request.state.user_email = token_data.email
        request.state.role = token_data.role

        # Auto-provision Tenant/User records
        if token_data.team_id:
            await self._ensure_tenant_and_user(token_data)

        response = await call_next(request)
        return response

    async def _ensure_tenant_and_user(self, token_data: TokenData) -> None:
        """Create Tenant and User records if they don't exist yet."""
        async with async_session_factory() as session:
            team_uuid = UUID(token_data.team_id)
            user_uuid = UUID(token_data.user_id)

            # Check / create Tenant
            result = await session.execute(
                select(Tenant).where(Tenant.id == team_uuid)
            )
            tenant = result.scalar_one_or_none()
            if not tenant:
                tenant = Tenant(
                    id=team_uuid,
                    name=f"Team {token_data.team_id[:8]}",
                    slug=f"team-{token_data.team_id[:8].lower()}",
                    is_active=True,
                )
                session.add(tenant)

            # Check / create User
            result = await session.execute(
                select(User).where(User.id == user_uuid)
            )
            user = result.scalar_one_or_none()
            if not user:
                user = User(
                    id=user_uuid,
                    tenant_id=team_uuid,
                    email=token_data.email or f"user-{token_data.user_id[:8]}@auto.local",
                    display_name=token_data.email or "User",
                    role=token_data.role or "member",
                    is_active=True,
                    last_login_at=datetime.utcnow(),
                )
                session.add(user)
            else:
                user.last_login_at = datetime.utcnow()

            await session.commit()
