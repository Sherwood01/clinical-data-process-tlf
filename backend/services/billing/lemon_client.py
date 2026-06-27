"""Lemon Squeezy API client wrapper for SaaS billing."""
import httpx
import logging
from typing import Dict, Any, Optional

from backend.core.config import settings

logger = logging.getLogger("lemon-client")


class LemonSqueezyClient:
    """Lemon Squeezy API 客户端，用于管理收银台及订阅。"""

    def __init__(self):
        self.api_key = settings.LEMON_SQUEEZY_API_KEY
        self.store_id = settings.LEMON_SQUEEZY_STORE_ID
        self.base_url = "https://api.lemonsqueezy.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        }

    async def create_checkout(
        self,
        variant_id: str,
        tenant_id: str,
        user_id: str,
        plan_type: str,
        redirect_url: Optional[str] = None,
    ) -> Optional[str]:
        """创建 Lemon Squeezy 收银台链接。

        :param variant_id: Lemon Squeezy 商品变体 ID (套餐 ID)
        :param tenant_id: 租户 ID，用于付款成功后回调定位租户
        :param user_id: 发起付款的用户 ID，用于区分个人订阅或团队订阅发起人
        :param plan_type: 期望升级的套餐类型 ('pro', 'plus')
        :param redirect_url: 付款成功后的重定向回显链接
        :return: 收银台付款 URL 链接或 None
        """
        if not self.api_key or not self.store_id:
            logger.error("Lemon Squeezy API Key 或 Store ID 未配置")
            return None

        url = f"{self.base_url}/checkouts"
        
        # 组装符合 JSON:API 规范的 Payload
        payload = {
            "data": {
                "type": "checkouts",
                "attributes": {
                    "custom_data": {
                        "tenant_id": tenant_id,
                        "user_id": user_id,
                        "plan_type": plan_type,
                    }
                },
                "relationships": {
                    "store": {
                        "data": {
                            "type": "stores",
                            "id": str(self.store_id)
                        }
                    },
                    "variant": {
                        "data": {
                            "type": "variants",
                            "id": str(variant_id)
                        }
                    }
                }
            }
        }

        # 如果提供了回调跳转地址，则追加到收银台属性中
        if redirect_url:
            payload["data"]["attributes"]["redirect_url"] = redirect_url

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=self.headers)
                
                if resp.status_code != 201:
                    logger.error(f"创建 Checkout 失败: {resp.status_code} - {resp.text}")
                    return None
                
                data = resp.json()
                checkout_url = data.get("data", {}).get("attributes", {}).get("url")
                return checkout_url
        except Exception as e:
            logger.exception(f"创建 Lemon Squeezy Checkout 请求异常: {e}")
            return None


# 实例化单例客户端
lemon_client = LemonSqueezyClient()
