"""SuperTokens SDK initialization.

Called at import time to configure SuperTokens recipes before the
FastAPI app starts.  The OAuth provider list is intentionally minimal
— add Google / GitHub / Microsoft client_id + client_secret here when
the user provides credentials.
"""
from supertokens_python import init, InputAppInfo, SupertokensConfig
from supertokens_python.recipe import thirdpartyemailpassword, session
from supertokens_python.recipe.thirdpartyemailpassword import (
    Google,
    Github,
)

from backend.core.config import settings

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
        thirdpartyemailpassword.init(
            providers=[
                # Email + password is built-in; OAuth providers require
                # client_id + client_secret.  Uncomment and fill in
                # when you register each app:
                #
                # Google(client_id="...", client_secret="..."),
                # Github(client_id="...", client_secret="..."),
                #
                # Microsoft requires a custom provider config — see:
                # supertokens.com/docs/thirdparty/microsoft/
            ],
        ),
        session.init(
            cookie_secure=False,  # True in prod with HTTPS
            cookie_same_site="lax",
        ),
    ],
)
