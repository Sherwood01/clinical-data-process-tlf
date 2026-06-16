"""JWT authentication middleware for FastAPI.

Extracts and validates Stack Auth JWT tokens from incoming requests,
injects tenant context into request state, and auto-provisions
Tenant/User records in the application database on first login.
"""
from typing import Optional, Callable
from uuid import UUID
from datetime import datetime

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select

from backend.core.security import verify_stack_auth_token, TokenData
from backend.db.session import async_session_factory
from backend.db.models import Tenant, User


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware that validates JWT and sets tenant context."""

    # Paths that don't require authentication
    PUBLIC_PATHS = {
        "/api/v1/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip auth for public paths
        if request.url.path in self.PUBLIC_PATHS or request.url.path.startswith("/api/v1/auth/"):
            return await call_next(request)

        # Extract token
        auth_header = request.headers.get("Authorization", "")
        print(f"DEBUG AUTH: {auth_header[:200] if auth_header else 'None'}", flush=True)
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid Authorization header"},
            )

        token = auth_header.removeprefix("Bearer ")

        # Verify token
        token_data = await verify_stack_auth_token(token)
        if token_data is None:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"},
            )

        # Set tenant context on request state
        request.state.user_id = token_data.user_id
        request.state.tenant_id = token_data.team_id  # Stack Auth team = our tenant
        request.state.user_email = token_data.email
        request.state.role = token_data.role

        # Auto-provision Tenant/User records in the application database.
        # Stack Auth manages users/teams on its side, but our app's models
        # (tenants, users tables) have FK constraints that must be satisfied.
        if token_data.team_id:
            await self._ensure_tenant_and_user(token_data)

        response = await call_next(request)
        return response

    async def _ensure_tenant_and_user(self, token_data: TokenData) -> None:
        """Create Tenant and User records if they don't exist yet.

        Called on every authenticated request so that even if a user registered
        via Stack Auth while the API was offline, they get provisioned on first
        contact.
        """
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
