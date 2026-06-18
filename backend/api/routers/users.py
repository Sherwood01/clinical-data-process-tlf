"""User-related endpoints."""
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me")
async def get_current_user(request: Request):
    """Return the current authenticated user's info.

    The AuthMiddleware already populates request.state from the
    SuperTokens session (including email fetched from SuperTokens
    core if not in the access token payload).
    """
    email = getattr(request.state, "user_email", None)
    user_id = getattr(request.state, "user_id", None)

    if not user_id:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

    return {
        "user_id": user_id,
        "email": email,
        "display_name": email or user_id,
    }
