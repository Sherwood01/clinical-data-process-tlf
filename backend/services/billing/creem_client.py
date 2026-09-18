"""Creem API client wrapper for SaaS billing."""
import httpx
import logging
from typing import Dict, Any, Optional

from backend.core.config import settings

logger = logging.getLogger("creem-client")


class CreemClient:
    """Creem 支付平台 API 客户端，用于管理收银台与订阅。"""

    def __init__(self):
        """初始化客户端，自动提取 API 密钥并自适应决定 API Base URL。"""
        self.api_key = settings.CREEM_API_KEY
        
        # 根据 API 密钥是否包含 test 标识，自适应切换沙箱与生产地址
        if self.api_key and ("test" in self.api_key.lower()):
            self.base_url = "https://test-api.creem.io/v1"
            logger.info("Creem 客户端初始化：使用沙箱/测试模式 (test-api.creem.io)")
        else:
            self.base_url = "https://api.creem.io/v1"
            logger.info("Creem 客户端初始化：使用生产模式 (api.creem.io)")
            
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def create_checkout(
        self,
        product_id: str,
        tenant_id: str,
        user_id: str,
        plan_type: str,
        redirect_url: Optional[str] = None,
        user_email: Optional[str] = None,
    ) -> Optional[str]:
        """向 Creem API 发起请求，创建支付收银台会话链接。

        :param product_id: Creem 的商品/计划 (Product) ID
        :param tenant_id: 当前租户 ID，用于付款成功后回调归属定位
        :param user_id: 发起付款的用户 ID，用于区分个人订阅或团队订阅发起人
        :param plan_type: 期望升级的套餐类型 ('pro', 'plus')
        :param redirect_url: 付款成功后的重定向回显链接 (success_url)
        :param user_email: 可选，当前登录用户的邮箱地址，用于预填收银台以提升支付体验
        :return: 成功返回收银台支付 URL 链接，失败返回 None
        """
        if not self.api_key:
            logger.error("Creem API 密钥 (CREEM_API_KEY) 未配置，无法生成支付链接")
            return None

        url = f"{self.base_url}/checkouts"
        
        # 组装 Creem 要求的 JSON Payload
        payload = {
            "product_id": product_id,
            "metadata": {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "plan_type": plan_type,
            }
        }
        
        if redirect_url:
            payload["success_url"] = redirect_url
            
        if user_email:
            payload["customer"] = {
                "email": user_email
            }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=self.headers)
                
                if resp.status_code not in [200, 201]:
                    logger.error(
                        f"创建 Creem Checkout 失败: 状态码={resp.status_code}, 详情={resp.text}"
                    )
                    return None
                
                data = resp.json()
                # 提取返回体中的 checkout 链接，优先读取 checkout_url，并兼容 url 及其嵌套结构
                checkout_url = (
                    data.get("checkout_url") or 
                    data.get("url") or 
                    data.get("data", {}).get("checkout_url") or 
                    data.get("data", {}).get("url")
                )
                
                if not checkout_url:
                    logger.error(f"Creem API 返回的响应体中未包含支付 URL: {data}")
                    return None
                    
                return checkout_url
                
        except Exception as e:
            logger.exception(f"向 Creem 创建 Checkout 会话请求时发生异常: {e}")
            return None


# 实例化单例客户端
creem_client = CreemClient()
