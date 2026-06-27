"""Authentication middleware for FastAPI.

Verifies SuperTokens session tokens from incoming requests,
injects tenant context into request state, and auto-provisions
Tenant/User records in the application database on first login.

Replaced the old Stack-Auth JWT verification.
"""
from typing import Callable
from uuid import UUID
from datetime import datetime, timedelta, timezone

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
        # Skip auth for public paths, Webhooks, and SuperTokens auth endpoints
        if (
            request.url.path in self.PUBLIC_PATHS
            or request.url.path == "/api/v1/billing/webhook"
            or request.url.path.startswith("/api/v1/auth/")
        ):
            return await call_next(request)


        # Verify session via SuperTokens SDK (supports both cookie and header transfer methods)
        token_data = await verify_supertokens_session(request)
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

        # Auto-provision Tenant/User records and resolve plan types
        if token_data.team_id:
            tenant_plan, user_plan = await self._ensure_tenant_and_user(token_data)
            request.state.tenant_plan = tenant_plan
            request.state.user_plan = user_plan
        else:
            request.state.tenant_plan = "free"
            request.state.user_plan = "free"

        response = await call_next(request)
        return response

    async def _ensure_tenant_and_user(self, token_data: TokenData) -> tuple[str, str]:
        """Create Tenant and User records if they don't exist yet, return plan types."""
        async with async_session_factory() as session:
            team_uuid = UUID(token_data.team_id)
            user_uuid = UUID(token_data.user_id)
            now = datetime.now(timezone.utc)

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
                    plan_type="free",
                    current_period_end=now + timedelta(days=30),
                    monthly_usage_count=0
                )
                session.add(tenant)
                tenant_plan = "free"
            else:
                tenant_plan = tenant.plan_type or "free"
                # 免费版套餐进行 30 天惰性用量清零
                if tenant_plan == "free":
                    if tenant.current_period_end is None or tenant.current_period_end < now:
                        tenant.monthly_usage_count = 0
                        tenant.current_period_end = now + timedelta(days=30)

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
                    last_login_at=now,
                    plan_type="free",
                    current_period_end=now + timedelta(days=30),
                    monthly_usage_count=0
                )
                session.add(user)
                user_plan = "free"
            else:
                user.last_login_at = now
                user_plan = user.plan_type or "free"
                # 免费版个人账号进行 30 天惰性用量清零
                if user_plan == "free":
                    if user.current_period_end is None or user.current_period_end < now:
                        user.monthly_usage_count = 0
                        user.current_period_end = now + timedelta(days=30)

            await session.commit()
            return tenant_plan, user_plan
