"""Session verification using SuperTokens.

Uses the SDK's verify_session to validate access tokens from incoming
requests, then extracts user info from the session object.
"""
import logging
from typing import Optional, Dict
from dataclasses import dataclass

import httpx
from supertokens_python.recipe.session.recipe import SessionRecipe
from supertokens_python.framework.fastapi.fastapi_request import FastApiRequest
from supertokens_python.recipe.session.interfaces import SessionContainer
from fastapi import Request

from backend.core.config import settings

logger = logging.getLogger(__name__)

# Simple in-memory cache: user_id -> email
_email_cache: Dict[str, str] = {}


@dataclass
class TokenData:
    """Extracted data from a validated session."""
    user_id: str
    team_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


async def _fetch_email_from_supertokens(user_id: str) -> Optional[str]:
    """Query SuperTokens core for the user's real email."""
    if user_id in _email_cache:
        return _email_cache[user_id]

    try:
        supertokens_url = settings.SUPERTOKENS_CONNECTION_URI.rstrip("/")
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{supertokens_url}/recipe/user?userId={user_id}",
                headers={"api-key": settings.SUPERTOKENS_API_KEY},
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "OK":
                    user = data.get("user", {})
                    emails = user.get("emails", [])
                    # Use first email from loginMethods if emails array is empty
                    if not emails:
                        login_methods = user.get("loginMethods", [])
                        for lm in login_methods:
                            if lm.get("email"):
                                emails = [lm["email"]]
                                break
                    if emails:
                        email = emails[0]
                        _email_cache[user_id] = email
                        return email
    except Exception as e:
        logger.warning("Failed to fetch email from SuperTokens core: %s", e)

    return None


async def verify_supertokens_session(
    request: Request,
) -> Optional[TokenData]:
    """Verify a SuperTokens session and extract user info.

    Delegates token extraction to the SDK (supports both cookie and
    Authorization header transfer methods).
    """
    try:
        logger.info(
            "verify_supertokens_session called: method=%s path=%s content_type=%s",
            request.method,
            request.url.path,
            request.headers.get("content-type", "none"),
        )

        # Build a FastApiRequest wrapper and ask the SDK to verify the session
        fastapi_req = FastApiRequest(request)
        session: SessionContainer = await SessionRecipe.get_instance().verify_session(
            request=fastapi_req,
            anti_csrf_check=False,
            session_required=True,
            check_database=True,
            override_global_claim_validators=None,
            user_context={},
        )

        user_id = session.user_id
        payload = session.get_access_token_payload()

        # Fetch real email from SuperTokens core if not in payload
        email = payload.get("email") or payload.get("x-email-from-idp")

        if not email:
            email = await _fetch_email_from_supertokens(user_id)
            # Write email back into the access token payload so frontend
            # can read it from session.accessTokenPayload.email on next request
            if email:
                try:
                    await session.merge_into_access_token_payload({"email": email}, {})
                except Exception:
                    pass  # non-critical; email still in TokenData for this request

        logger.info(
            "verify_supertokens_session SUCCESS: user_id=%s email=%s",
            user_id, email,
        )

        # ─────────────────────────────────────────────────────────────
        # 一劳永逸机制：邮箱主键锚定映射 (Email-to-DB-Tenant Anchor)
        # 如果获取到了用户的真实 email，优先从应用数据库 users 表中按 email 反查出
        # 物理登记的真实 User ID / Tenant ID。
        # 确保不论 SuperTokens 分配何种虚拟 ID，主账号的数据永远 100% 精确锚定！
        # ─────────────────────────────────────────────────────────────
        resolved_tenant_id = user_id
        resolved_user_id = user_id
        if email:
            try:
                from backend.db.session import async_session_factory
                from backend.db.models import User
                from sqlalchemy import select
                async with async_session_factory() as db_session:
                    db_user_res = await db_session.execute(
                        select(User).where(User.email == email)
                    )
                    db_user = db_user_res.scalar_one_or_none()
                    if db_user:
                        resolved_user_id = str(db_user.id)
                        resolved_tenant_id = str(db_user.tenant_id)
            except Exception as ex:
                logger.warning("Failed to anchor user_id by email: %s", ex)

        return TokenData(
            user_id=resolved_user_id,
            team_id=resolved_tenant_id,
            email=email,  # May be None if we couldn't fetch it
            role="member",
        )
    except Exception as e:
        logger.error(
            "verify_supertokens_session FAILED: method=%s path=%s error=%s",
            request.method,
            request.url.path,
            str(e),
            exc_info=True,
        )
        return None
