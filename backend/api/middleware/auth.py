"""JWT authentication middleware for FastAPI.

Extracts and validates Stack Auth JWT tokens from incoming requests,
and injects tenant context into request state.
"""
from typing import Optional, Callable

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.security import verify_stack_auth_token


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

        response = await call_next(request)
        return response
