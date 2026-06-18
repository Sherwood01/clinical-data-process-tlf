"""Session verification using SuperTokens.

Replaced the old Stack-Auth JWT + JWKS approach.
"""
from typing import Optional
from dataclasses import dataclass

from supertokens_python.recipe.session.functions import get_session
from supertokens_python.recipe.thirdpartyemailpassword.asyncio import get_user_by_id
from fastapi import Request


@dataclass
class TokenData:
    """Extracted data from a validated session."""
    user_id: str
    team_id: Optional[str] = None  # Maps to tenant_id (same as user_id for now)
    email: Optional[str] = None
    role: Optional[str] = None


async def verify_supertokens_session(
    request: Request, token: str
) -> Optional[TokenData]:
    """Verify a SuperTokens session token and extract user info.

    Calls SuperTokens Core via the SDK to validate the session,
    then fetches the user's email from the thirdpartyemailpassword recipe.
    """
    try:
        session = await get_session(
            request,
            session_token=token,
            check_database=True,
        )
        user_id = session.get_user_id()

        # Fetch email from supertokens user info
        email = None
        try:
            user_info = await get_user_by_id(user_id)
            if user_info:
                email = user_info.email
        except Exception:
            pass

        return TokenData(
            user_id=user_id,
            team_id=user_id,  # Each user is their own tenant (1:1)
            email=email or f"user-{user_id[:8]}@auto.local",
            role="member",
        )
    except Exception:
        return None
