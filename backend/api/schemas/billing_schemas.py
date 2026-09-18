"""Pydantic schemas for SaaS billing and subscription validation."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class CheckoutRequest(BaseModel):
    """申请收银台付款链接的请求校验模型。"""
    variant_id: str = Field(..., description="Lemon Squeezy 商品变体套餐 ID")
    plan_type: str = Field(..., description="目标升级套餐类型 ('pro', 'plus')")
    redirect_url: Optional[str] = Field(None, description="付款成功后的跳转回显地址")


class CheckoutResponse(BaseModel):
    """申请收银台付款链接的返回校验模型。"""
    checkout_url: str = Field(..., description="Lemon Squeezy 收银台付款跳转链接")


class LemonWebhookCustomData(BaseModel):
    """Lemon Squeezy 自定义携带的数据。"""
    tenant_id: str = Field(..., description="所属租户 ID")
    user_id: str = Field(..., description="购买人的用户 ID")
    plan_type: str = Field(..., description="开通的订阅计划等级")


class LemonWebhookMeta(BaseModel):
    """Lemon Squeezy Webhook 头部元数据。"""
    event_name: str = Field(..., description="回调事件类型")
    custom_data: Optional[LemonWebhookCustomData] = Field(None, description="自定义元数据")


class LemonSubscriptionUrls(BaseModel):
    """Lemon Squeezy 订阅相关的用户链接。"""
    update_payment_method: Optional[str] = Field(None, description="更新支付方式链接")
    customer_portal: Optional[str] = Field(None, description="账单及订阅管理链接")


class LemonSubscriptionAttributes(BaseModel):
    """Lemon Squeezy 订阅的详细属性。"""
    store_id: int
    customer_id: int
    status: str = Field(..., description="订阅状态 ('active', 'past_due', etc.)")
    renews_at: Optional[str] = Field(None, description="下一次续期时间")
    ends_at: Optional[str] = Field(None, description="订阅结束时间")
    urls: Optional[LemonSubscriptionUrls] = Field(None, description="操作链接")


class LemonWebhookData(BaseModel):
    """Lemon Squeezy Webhook 数据体。"""
    id: str = Field(..., description="Lemon Squeezy 订阅 ID")
    type: str = Field(..., description="数据类型，这里应为 'subscriptions'")
    attributes: LemonSubscriptionAttributes


class LemonWebhookPayload(BaseModel):
    """Lemon Squeezy Webhook 整体 Payload 模型。"""
    meta: LemonWebhookMeta
    data: LemonWebhookData

    class Config:
        extra = "ignore"  # 忽略其他多余的 Lemon Squeezy 回调属性，保证接口兼容
