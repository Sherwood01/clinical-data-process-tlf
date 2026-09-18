"""SuperTokens SDK initialization.

Called at import time to configure SuperTokens recipes before the
FastAPI app starts.  OAuth providers are configured from env vars.
"""
from typing import Any, Dict, List

from supertokens_python import init, InputAppInfo, SupertokensConfig
from supertokens_python.recipe import session
from supertokens_python.recipe.thirdparty import init as thirdparty_init
from supertokens_python.recipe.thirdparty import (
    SignInAndUpFeature,
    ProviderInput,
    ProviderConfig,
    ProviderClientConfig,
)
from supertokens_python.recipe.thirdparty.provider import UserInfoMap, UserFields
from supertokens_python.recipe.thirdparty.providers.google import Google as GoogleProvider
from supertokens_python.recipe.thirdparty.providers.github import Github as GithubProvider
from supertokens_python.recipe.thirdparty.providers.custom import NewProvider
from supertokens_python.recipe.emailpassword import (
    init as emailpassword_init,
    EmailPasswordOverrideConfig,
)
from supertokens_python.recipe.emailpassword.interfaces import (
    APIInterface,
    SignUpPostOkResult,
    SignInPostOkResult,
)
from supertokens_python.recipe.dashboard import init as dashboard_init

from backend.core.config import settings


def _override_ep_apis(original_implementation: APIInterface) -> APIInterface:
    """Override signup/signin to embed email into the access token payload.

    SuperTokens does NOT include `email` in the default access token claims,
    so every component that reads session.accessTokenPayload?.email would see
    undefined and fall back to the raw userId.  We merge it in at the earliest
    possible moment — right after account creation or sign-in.
    """
    original_sign_up = original_implementation.sign_up_post
    original_sign_in = original_implementation.sign_in_post

    async def sign_up_post(
        form_fields: List[Any],
        tenant_id: str,
        session_container: Any,
        should_try_linking_with_session_user: Any,
        api_options: Any,
        user_context: Dict[str, Any],
    ):
        resp = await original_sign_up(
            form_fields,
            tenant_id,
            session_container,
            should_try_linking_with_session_user,
            api_options,
            user_context,
        )
        if isinstance(resp, SignUpPostOkResult) and resp.session and resp.user.emails:
            await resp.session.merge_into_access_token_payload(
                {"email": resp.user.emails[0]}, user_context
            )
        return resp

    async def sign_in_post(
        form_fields: List[Any],
        tenant_id: str,
        session_container: Any,
        should_try_linking_with_session_user: Any,
        api_options: Any,
        user_context: Dict[str, Any],
    ):
        resp = await original_sign_in(
            form_fields,
            tenant_id,
            session_container,
            should_try_linking_with_session_user,
            api_options,
            user_context,
        )
        if isinstance(resp, SignInPostOkResult) and resp.session and resp.user.emails:
            await resp.session.merge_into_access_token_payload(
                {"email": resp.user.emails[0]}, user_context
            )
        return resp

    original_implementation.sign_up_post = sign_up_post
    original_implementation.sign_in_post = sign_in_post
    return original_implementation


provider_inputs: list[ProviderInput] = []

if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    inp = ProviderInput(
        config=ProviderConfig(
            third_party_id="google",
            clients=[
                ProviderClientConfig(
                    client_id=settings.GOOGLE_CLIENT_ID,
                    client_secret=settings.GOOGLE_CLIENT_SECRET,
                )
            ],
        )
    )
    # Google() applies OIDC discovery endpoint and other defaults to the input
    GoogleProvider(inp)
    provider_inputs.append(inp)

if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
    inp = ProviderInput(
        config=ProviderConfig(
            third_party_id="github",
            clients=[
                ProviderClientConfig(
                    client_id=settings.GITHUB_CLIENT_ID,
                    client_secret=settings.GITHUB_CLIENT_SECRET,
                )
            ],
        )
    )
    GithubProvider(inp)
    provider_inputs.append(inp)

if settings.MICROSOFT_CLIENT_ID and settings.MICROSOFT_CLIENT_SECRET:
    inp = ProviderInput(
        config=ProviderConfig(
            third_party_id="microsoft",
            name="Microsoft",
            authorization_endpoint="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            authorization_endpoint_query_params={
                "scope": "openid offline_access email profile",
            },
            token_endpoint="https://login.microsoftonline.com/common/oauth2/v2.0/token",
            user_info_endpoint="https://graph.microsoft.com/v1.0/me",
            user_info_map=UserInfoMap(
                from_user_info_api=UserFields(
                    user_id="id",
                    email="userPrincipalName",
                )
            ),
            clients=[
                ProviderClientConfig(
                    client_id=settings.MICROSOFT_CLIENT_ID,
                    client_secret=settings.MICROSOFT_CLIENT_SECRET,
                )
            ],
        )
    )
    # NewProvider wraps the ProviderInput into a custom GenericProvider
    NewProvider(inp)
    provider_inputs.append(inp)

init(
    app_info=InputAppInfo(
        app_name="TLF",
        api_domain=settings.SUPERTOKENS_API_DOMAIN,
        website_domain=settings.SUPERTOKENS_WEBSITE_DOMAIN,
        api_base_path="/api/v1/auth",
        website_base_path="/auth",
    ),
    supertokens_config=SupertokensConfig(
        connection_uri=settings.SUPERTOKENS_CONNECTION_URI,
        api_key=settings.SUPERTOKENS_API_KEY,
    ),
    framework="fastapi",
    mode="wsgi",
    recipe_list=[
        emailpassword_init(
            override=EmailPasswordOverrideConfig(apis=_override_ep_apis),
        ),
        thirdparty_init(
            sign_in_and_up_feature=SignInAndUpFeature(providers=provider_inputs),
        ),
        session.init(
            cookie_secure=False,
            cookie_same_site="lax",
        ),
        dashboard_init(api_key=settings.SUPERTOKENS_API_KEY),
    ],
)
