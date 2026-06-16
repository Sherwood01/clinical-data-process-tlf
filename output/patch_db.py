import asyncio
import os
import asyncpg

async def main():
    db_url = "postgresql://postgres:postgres@postgres:5432/tlf_saas"
    print(f"Connecting to {db_url}...")
    try:
        conn = await asyncpg.connect(db_url)
        
        # 1. 强制将用户新建的两个项目 onboarding 状态设置为 completed
        print("Completing onboarding for custom projects...")
        res1 = await conn.execute("""
            UPDATE "Project" 
            SET "onboardingStatus" = 'completed', "onboardingState" = NULL 
            WHERE id IN ('493caf01-c7ec-42f9-85d6-1780b79bf824', 'a37ebd2f-df8a-463a-bf7d-82c562a7385e');
        """)
        print(f"Update projects onboarding status: {res1}")

        # 2. 将默认的 internal 项目的拥有者团队修改为用户的 Team ID
        print("Assigning 'internal' project ownership to user's team '6ea8b8de-ad1e-4eb5-ad4b-ff3ac4c38a95'...")
        res2 = await conn.execute("""
            UPDATE "Project" 
            SET "ownerTeamId" = '6ea8b8de-ad1e-4eb5-ad4b-ff3ac4c38a95' 
            WHERE id = 'internal';
        """)
        print(f"Update internal project owner: {res2}")

        await conn.close()
        print("Database patching completed successfully!")
    except Exception as e:
        print(f"Database patch failed: {e}")

if __name__ == '__main__':
    asyncio.run(main())
