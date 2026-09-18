"""Configuration and initialization for the AI Agent大语言模型 (Supports Cloudflare Workers AI & DeepSeek)."""
import os
import logging
from openai import AsyncOpenAI
from backend.core.config import settings

logger = logging.getLogger("ai-config")

# Retrieve credentials
cf_account_id = settings.CLOUDFLARE_ACCOUNT_ID or os.environ.get("CLOUDFLARE_ACCOUNT_ID")
cf_api_token = settings.CLOUDFLARE_API_TOKEN or os.environ.get("CLOUDFLARE_API_TOKEN")
cf_model = settings.CLOUDFLARE_AI_MODEL or os.environ.get("CLOUDFLARE_AI_MODEL") or "@cf/zai-org/glm-4.7-flash"

deepseek_key = settings.DEEPSEEK_API_KEY or os.environ.get("DEEPSEEK_API_KEY")

if cf_account_id and cf_api_token:
    logger.info("Initializing AsyncOpenAI client targeting Cloudflare Workers AI endpoint...")
    base_url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/ai/v1"
    api_key = cf_api_token
    MODEL_NAME = cf_model
else:
    logger.info("Initializing AsyncOpenAI client targeting DeepSeek endpoint...")
    base_url = "https://api.deepseek.com"
    api_key = deepseek_key or "mock-key-for-local-testing"
    MODEL_NAME = settings.DEEPSEEK_MODEL or "deepseek-v4-flash"

deepseek_client = AsyncOpenAI(
    api_key=api_key,
    base_url=base_url,
    timeout=60.0
)

