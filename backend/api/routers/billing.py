"""Billing and subscription router — handles Creem checkout & Webhooks."""
import hmac
import hashlib
import json
import logging
from uuid import UUID
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from dateutil.parser import parse as parse_date

from backend.core.config import settings
from backend.db.session import get_db
from backend.db.models import Tenant, User
from backend.api.schemas.billing_schemas import CheckoutRequest, CheckoutResponse
from backend.api.routers.studies import get_tenant_id, get_user_id
from backend.services.billing.creem_client import creem_client

logger = logging.getLogger("billing-router")

router = APIRouter(prefix="/billing")


@router.post("/checkout", response_model=CheckoutResponse, status_code=200)
async def generate_checkout_url(
    req: CheckoutRequest,
    request: Request,
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_user_id),
):
    """为当前登录用户或租户申请 Creem 支付收银台链接。

    参数:
        req: 包含目标 variant_id (即 Creem 的 product_id) 与 redirect_url 的请求体
        request: FastAPI 请求对象，用于读取当前用户的 Session 状态
        tenant_id: 由 Depends 注入的当前租户 ID
        user_id: 由 Depends 注入的当前用户 ID
    """
    # 尝试从请求状态中获取当前登录用户的邮箱，用于收银台预填
    user_email = getattr(request.state, "user_email", None)

    checkout_url = await creem_client.create_checkout(
        product_id=req.variant_id,  # 前端传入的 variant_id 对应为 Creem 的 product_id
        tenant_id=str(tenant_id),
        user_id=str(user_id),
        plan_type=req.plan_type,
        redirect_url=req.redirect_url,
        user_email=user_email,
    )
    
    if not checkout_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成 Creem 支付跳转链接失败，请稍后重试或联系客服。"
        )
        
    return CheckoutResponse(checkout_url=checkout_url)


@router.post("/webhook", status_code=200)
async def handle_creem_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """接收并处理 Creem 支付平台的异步状态通知 (Webhook)。

    参数:
        request: FastAPI 请求对象，包含 Raw Body 字节流与 Header 签名
        db: 数据库异步会话
    """
    body = await request.body()
    signature = request.headers.get("creem-signature")

    # 1. 安全性校验：验证 Creem 签名
    if not signature:
        logger.error("Creem Webhook 请求缺少 creem-signature 签名请求头")
        raise HTTPException(status_code=401, detail="Missing signature header")

    if not settings.CREEM_WEBHOOK_SECRET:
        logger.error("系统未配置 CREEM_WEBHOOK_SECRET")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    # 计算本地 HMAC-SHA256 签名并核对
    local_sig = hmac.new(
        settings.CREEM_WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(local_sig, signature):
        logger.error(f"Creem Webhook 签名校验失败: header={signature}, local={local_sig}")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 2. 解析 JSON 数据体
    try:
        payload = json.loads(body)
    except Exception as e:
        logger.error(f"解析 Creem Webhook JSON 数据失败: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    event_type = payload.get("eventType")
    data_obj = payload.get("object", {})
    metadata = data_obj.get("metadata", {})

    if not event_type or not metadata:
        # 兼容握手测试事件
        logger.info(f"收到 Creem 事件: {event_type}，但缺少 metadata，忽略处理")
        return {"status": "ignored"}

    tenant_id_str = metadata.get("tenant_id")
    user_id_str = metadata.get("user_id")
    plan_type = metadata.get("plan_type")

    if not tenant_id_str or not user_id_str or not plan_type:
        logger.warning(f"Creem Webhook 携带的元数据不完整: {metadata}")
        return {"status": "ignored_incomplete_metadata"}

    # 提取订阅/订单唯一标识
    subscription_id = data_obj.get("id") or data_obj.get("subscription_id")
    sub_status = data_obj.get("status", "active")
    
    # 提取账期结束时间 (兼容 ends_at, expires_at 等属性)
    ends_at_str = data_obj.get("ends_at") or data_obj.get("expires_at") or data_obj.get("current_period_end")
    now_utc = datetime.now(timezone.utc)
    period_end = None
    
    if ends_at_str:
        try:
            period_end = parse_date(ends_at_str)
        except Exception:
            pass
            
    # 兜底设置：默认账期为 30 天后
    if not period_end:
        period_end = now_utc + timedelta(days=30)

    # 提取 Customer Portal 链接 (若 Creem 返回了管理链接，我们将其保存以便用户升级/退订)
    portal_url = data_obj.get("portal_url") or data_obj.get("customer_portal")

    logger.info(
        f"处理 Creem 订阅事件: event={event_type}, sub_id={subscription_id}, "
        f"status={sub_status}, tenant_id={tenant_id_str}, user={user_id_str}, plan={plan_type}"
    )

    # 3. 分发并更新租户版（Plus/Enterprise）或个人版（Pro）的订阅套餐状态
    if plan_type in ["plus", "enterprise"]:
        # 团队/租户订阅 -> 更新 Tenant 属性
        tenant_uuid = UUID(tenant_id_str)
        result = await db.execute(select(Tenant).where(Tenant.id == tenant_uuid))
        tenant = result.scalar_one_or_none()

        if not tenant:
            logger.error(f"未找到指定的订阅租户: {tenant_id_str}")
            raise HTTPException(status_code=404, detail="Tenant not found")

        if event_type in ["checkout.completed", "subscription.created", "subscription.updated"]:
            tenant.plan_type = plan_type
            tenant.lemon_subscription_id = subscription_id  # 沿用原有列来存放 Creem 订阅 ID
            tenant.subscription_status = sub_status
            tenant.current_period_end = period_end
            if portal_url and isinstance(tenant.settings, dict):
                tenant.settings["billing_portal_url"] = portal_url
        
        elif event_type == "subscription.cancelled":
            # 退订仅代表期满后不再续费，在此期间状态设为 cancelled，期满前不收回权益
            tenant.subscription_status = "cancelled"
        
        elif event_type in ["subscription.expired", "subscription.payment_failed"]:
            # 彻底到期或扣款失败，强制降级回 free 并清空用量
            tenant.plan_type = "free"
            tenant.subscription_status = sub_status
            tenant.current_period_end = None
            tenant.monthly_usage_count = 0

        await db.commit()

    elif plan_type == "pro":
        # 个人版订阅 -> 更新 User 属性
        user_uuid = UUID(user_id_str)
        result = await db.execute(select(User).where(User.id == user_uuid))
        user = result.scalar_one_or_none()

        if not user:
            logger.error(f"未找到指定的个人订阅用户: {user_id_str}")
            raise HTTPException(status_code=404, detail="User not found")

        if event_type in ["checkout.completed", "subscription.created", "subscription.updated"]:
            user.plan_type = plan_type
            user.lemon_subscription_id = subscription_id  # 沿用原列存放 Creem 订阅 ID
            user.subscription_status = sub_status
            user.current_period_end = period_end
        
        elif event_type == "subscription.cancelled":
            user.subscription_status = "cancelled"
        
        elif event_type in ["subscription.expired", "subscription.payment_failed"]:
            user.plan_type = "free"
            user.subscription_status = sub_status
            user.current_period_end = None
            user.monthly_usage_count = 0

        await db.commit()

    else:
        logger.warning(f"无法识别的计划类型等级: {plan_type}")

    return {"status": "success"}


@router.get("/status", status_code=200)
async def get_billing_status(
    request: Request,
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取当前租户与个人的订阅套餐级别、资源限额以及本月报告生成用量。

    参数:
        request: FastAPI 请求对象，包含由 AuthMiddleware 注入的 state。
        tenant_id: 当前租户 ID。
        user_id: 当前用户 ID。
        db: 数据库异步会话。
    """
    # 1. 查询数据库中最新的 Tenant 与 User 记录
    tenant_res = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_res.scalar_one_or_none()

    user_res = await db.execute(select(User).where(User.id == user_id))
    user = user_res.scalar_one_or_none()

    if not tenant or not user:
        raise HTTPException(status_code=404, detail="租户或用户记录不存在")

    # 定义限额常量（避免魔法数字）
    # 1. Study 数量限额
    LIMIT_STUDIES_FREE = 1
    LIMIT_STUDIES_PRO = 50
    LIMIT_STUDIES_PLUS = 200
    LIMIT_STUDIES_ENTERPRISE = 999999  # 代表无限

    # 2. 每月 TLF 报告生成限额
    LIMIT_TLFS_FREE = 10
    LIMIT_TLFS_PRO = 500
    LIMIT_TLFS_PLUS = 5000
    LIMIT_TLFS_ENTERPRISE = 999999  # 代表无限

    tenant_plan = tenant.plan_type or "free"
    user_plan = user.plan_type or "free"

    # 计算租户限额
    tenant_study_limit = LIMIT_STUDIES_FREE
    tenant_tlf_limit = LIMIT_TLFS_FREE
    if tenant_plan == "plus":
        tenant_study_limit = LIMIT_STUDIES_PLUS
        tenant_tlf_limit = LIMIT_TLFS_PLUS
    elif tenant_plan == "enterprise":
        tenant_study_limit = LIMIT_STUDIES_ENTERPRISE
        tenant_tlf_limit = LIMIT_TLFS_ENTERPRISE

    # 计算用户个人限额
    user_study_limit = LIMIT_STUDIES_FREE
    user_tlf_limit = LIMIT_TLFS_FREE
    if user_plan == "pro":
        user_study_limit = LIMIT_STUDIES_PRO
        user_tlf_limit = LIMIT_TLFS_PRO

    # 提取 Customer Portal 链接
    billing_portal_url = None
    if isinstance(tenant.settings, dict):
        billing_portal_url = tenant.settings.get("billing_portal_url")

    # 兼容处理带时区日期的 ISO 序列化格式
    tenant_end_iso = None
    if tenant.current_period_end:
        # 确保带时区的 datetime 序列化正常，若不带时区，则统一追加 UTC 字符
        t_end = tenant.current_period_end
        if t_end.tzinfo is None:
            t_end = t_end.replace(tzinfo=timezone.utc)
        tenant_end_iso = t_end.isoformat()

    user_end_iso = None
    if user.current_period_end:
        u_end = user.current_period_end
        if u_end.tzinfo is None:
            u_end = u_end.replace(tzinfo=timezone.utc)
        user_end_iso = u_end.isoformat()

    return {
        "tenant": {
            "plan_type": tenant_plan,
            "subscription_status": tenant.subscription_status,
            "current_period_end": tenant_end_iso,
            "monthly_usage_count": tenant.monthly_usage_count,
            "max_studies": tenant_study_limit,
            "max_tlfs": tenant_tlf_limit,
            "billing_portal_url": billing_portal_url,
        },
        "user": {
            "plan_type": user_plan,
            "subscription_status": user.subscription_status,
            "current_period_end": user_end_iso,
            "monthly_usage_count": user.monthly_usage_count,
            "max_studies": user_study_limit,
            "max_tlfs": user_tlf_limit,
        }
    }
