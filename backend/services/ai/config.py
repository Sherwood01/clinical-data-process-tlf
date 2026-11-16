"""Configuration and initialization for the AI Agent 大语言模型 (Supports Zhipu GLM, Cloudflare Workers AI & DeepSeek)."""
import os
import logging
from openai import AsyncOpenAI
from backend.core.config import settings

logger = logging.getLogger("ai-config")

# 1. 优先读取智谱 GLM / OpenAI 兼容接口配置
glm_key = settings.get_llm_api_key() or os.environ.get("API_KEY") or os.environ.get("GLM_API_KEY")
glm_base_url = settings.get_clean_llm_base_url()
glm_model = settings.get_llm_model() or os.environ.get("MODEL") or "glm-5.3-flash"

# 2. Cloudflare Workers AI 配置
cf_account_id = settings.CLOUDFLARE_ACCOUNT_ID or os.environ.get("CLOUDFLARE_ACCOUNT_ID")
cf_api_token = settings.CLOUDFLARE_API_TOKEN or os.environ.get("CLOUDFLARE_API_TOKEN")
cf_model = settings.CLOUDFLARE_AI_MODEL or os.environ.get("CLOUDFLARE_AI_MODEL") or "@cf/zai-org/glm-4.7-flash"

# 3. DeepSeek 配置
deepseek_key = settings.DEEPSEEK_API_KEY or os.environ.get("DEEPSEEK_API_KEY")

if glm_key:
    logger.info(f"Initializing AsyncOpenAI client targeting GLM/OpenAI endpoint: {glm_base_url}, model: {glm_model}...")
    base_url = glm_base_url
    api_key = glm_key
    MODEL_NAME = glm_model
elif cf_account_id and cf_api_token:
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
    timeout=90.0
)
ai_client = deepseek_client

