import hmac
import hashlib
import json
import asyncio
import httpx
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# 容器内部网络地址配置
LOCAL_DB_URL = "postgresql+asyncpg://postgres:postgres@postgres:5432/tlf_saas"
API_WEBHOOK_URL = "http://api:8000/api/v1/billing/webhook"
WEBHOOK_SECRET = "my_creem_webhook_secret_key"


async def get_first_tenant_from_local_db():
    """从本地开发数据库中查询现存的第一个租户 ID，若无则自动插入一条测试数据。"""
    try:
        engine = create_async_engine(LOCAL_DB_URL)
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT id, name, plan_type FROM tenants LIMIT 1"))
            row = result.fetchone()
            if row:
                return {
                    "id": str(row[0]),
                    "name": row[1],
                    "plan_type": row[2]
                }
            
            # 自动生成测试租户
            test_id = "00000000-0000-0000-0000-000000000001"
            print(f"\n[INFO] 本地数据库为空，正在自动插入测试租户和用户 (ID: {test_id})...")
            
            await conn.execute(text(
                "INSERT INTO tenants (id, name, slug, settings, is_active, plan_type, monthly_usage_count) "
                "VALUES (:id, 'Test Creem Team', 'test-creem-team', '{}', true, 'free', 0)"
            ), {"id": test_id})
            
            await conn.execute(text(
                "INSERT INTO users (id, tenant_id, email, display_name, role, is_active, plan_type, monthly_usage_count) "
                "VALUES (:id, :tenant_id, 'tester@creem.local', 'Creem Tester', 'admin', true, 'free', 0)"
            ), {"id": test_id, "tenant_id": test_id})
            
            return {
                "id": test_id,
                "name": "Test Creem Team",
                "plan_type": "free"
            }
    except Exception as e:
        print(f"[ERROR] 无法连接本地数据库并初始化测试数据: {e}")
        return None


async def verify_tenant_plan_in_db(tenant_id: str):
    """验证本地数据库中租户的套餐类型。"""
    try:
        engine = create_async_engine(LOCAL_DB_URL)
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT plan_type, lemon_subscription_id, subscription_status FROM tenants WHERE id = :id"),
                {"id": tenant_id}
            )
            row = result.fetchone()
            if row:
                return {
                    "plan_type": row[0],
                    "subscription_id": row[1],
                    "status": row[2]
                }
            return None
    except Exception as e:
        print(f"[ERROR] 验证数据库状态失败: {e}")
        return None


async def trigger_mock_webhook(tenant_id: str, user_id: str, plan_type: str = "plus"):
    """模拟 Creem Webhook 事件并向本地 API 发送签名数据。"""
    payload = {
        "eventType": "checkout.completed",
        "object": {
            "id": "sub_creem_test_998877",
            "status": "active",
            "ends_at": "2026-07-25T20:00:00Z",
            "metadata": {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "plan_type": plan_type
            }
        }
    }
    
    body_str = json.dumps(payload, separators=(',', ':'))
    
    # 计算 HMAC-SHA256 签名
    sig = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        body_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "creem-signature": sig,
        "Content-Type": "application/json"
    }
    
    print(f"\n[INFO] 正在向 {API_WEBHOOK_URL} 发送模拟的 checkout.completed 事件...")
    print(f"[INFO] 目标租户 ID: {tenant_id}, 计划开通等级: {plan_type}")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(API_WEBHOOK_URL, content=body_str, headers=headers)
        print(f"[INFO] API 响应状态码: {resp.status_code}")
        print(f"[INFO] API 响应内容: {resp.text}")
        return resp.status_code == 200


async def main():
    print("=== 开始 Creem Webhook 本地集成测试 ===")
    
    # 1. 获取本地数据库中的第一个租户，若无租户则自动插入一条测试记录
    tenant = await get_first_tenant_from_local_db()
    if not tenant:
        print("\n[ERROR] 无法局立测试租户，测试终止。")
        return
        
    print(f"\n[INFO] 成功获取本地测试租户:")
    print(f" - 租户 ID: {tenant['id']}")
    print(f" - 租户名称: {tenant['name']}")
    print(f" - 当前套餐: {tenant['plan_type']}")
    
    # 2. 模拟触发 Webhook 升级租户为 Plus 套餐
    success = await trigger_mock_webhook(
        tenant_id=tenant["id"],
        user_id=tenant["id"],
        plan_type="plus"
    )
    
    if not success:
        print("\n[ERROR] 触发 Webhook 接口报错，请检查 API 控制台日志。")
        return
        
    # 3. 验证数据库中的字段是否被成功修改
    print("\n[INFO] 正在等待数据库写入同步完成...")
    await asyncio.sleep(1.0)
    
    db_status = await verify_tenant_plan_in_db(tenant["id"])
    if db_status:
        print("\n[INFO] 数据库状态校验成功:")
        print(f" - 新的套餐级别 (plan_type): {db_status['plan_type']} (预期值: plus)")
        print(f" - 订阅 ID (lemon_subscription_id): {db_status['subscription_id']} (预期值: sub_creem_test_998877)")
        print(f" - 订阅状态 (status): {db_status['status']} (预期值: active)")
        
        if db_status["plan_type"] == "plus":
            print("\n>>> [SUCCESS] Creem Webhook 签名校验与租户套餐升级流程全部打通！测试成功！")
        else:
            print("\n>>> [FAIL] 数据库记录未能成功升级，请检查 API 容器的 Webhook 处理逻辑。")
    else:
        print("\n>>> [FAIL] 未能在数据库中查询到更新后的租户状态。")


if __name__ == "__main__":
    asyncio.run(main())
