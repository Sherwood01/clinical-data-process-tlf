import asyncio
import os
import asyncpg

async def main():
    db_url = "postgresql://postgres:postgres@postgres:5432/tlf_saas"
    print(f"Connecting to {db_url}...")
    try:
        conn = await asyncpg.connect(db_url)
        
        # 1. 查询所有公开表
        print("\n--- All Public Tables ---")
        rows = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema='public' 
            ORDER BY table_name;
        """)
        tables = [row['table_name'] for row in rows]
        print(", ".join(tables))

        # 2. 查询 Project / ApiKeySet 相关表
        print("\n--- Project Table ---")
        try:
            p_rows = await conn.fetch('SELECT * FROM "Project";')
            for r in p_rows:
                print(dict(r))
        except Exception as e:
            print(f"Failed to query Project: {e}")

        # 3. 查询 ApiKeySet 表
        print("\n--- ApiKeySet Table ---")
        try:
            a_rows = await conn.fetch('SELECT "projectId", id, "publishableClientKey", "description" FROM "ApiKeySet";')
            for r in a_rows:
                print(dict(r))
        except Exception as e:
            print(f"Failed to query ApiKeySet: {e}")

        # 4. 查询 User 相关的账号信息
        print("\n--- User Table ---")
        try:
            u_rows = await conn.fetch('SELECT id, email, "createdAt" FROM "User";')
            for r in u_rows:
                print(dict(r))
        except Exception as e:
            print(f"Failed to query User: {e}")

        await conn.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == '__main__':
    asyncio.run(main())
