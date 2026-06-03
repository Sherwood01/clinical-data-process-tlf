"""JWT validation using Stack Auth's JWKS endpoint."""
from typing import Optional
from dataclasses import dataclass

import httpx
import jwt
from jwt import PyJWKClient

from backend.core.config import settings


@dataclass
class TokenData:
    """Extracted data from a validated JWT."""
    user_id: str
    team_id: Optional[str] = None  # Maps to tenant_id
    email: Optional[str] = None
    role: Optional[str] = None


_jwk_client: Optional[PyJWKClient] = None


def _get_jwk_client() -> PyJWKClient:
    """Get or create the JWKS client (lazy init)."""
    global _jwk_client
    if _jwk_client is None:
        _jwk_client = PyJWKClient(settings.STACK_AUTH_JWKS_URL)
    return _jwk_client


async def verify_stack_auth_token(token: str) -> Optional[TokenData]:
    """Verify a Stack Auth JWT and extract user/team info.

    Stack Auth tokens contain:
      - sub: user_id
      - team_id: the active team/organization (maps to our tenant_id)
      - email: user email
    """
    try:
        jwks_client = _get_jwk_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.STACK_AUTH_AUDIENCE or None,
            issuer=settings.STACK_AUTH_ISSUER,
            options={"verify_exp": True},
        )

        return TokenData(
            user_id=payload.get("sub", ""),
            team_id=payload.get("team_id"),
            email=payload.get("email"),
            role=payload.get("role", "member"),
        )
    except Exception:
        return None


async def fetch_jwks_public_key() -> Optional[str]:
    """Fetch the JWKS public key material for manual validation."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(settings.STACK_AUTH_JWKS_URL)
            resp.raise_for_status()
            return resp.text
    except Exception:
        return None
