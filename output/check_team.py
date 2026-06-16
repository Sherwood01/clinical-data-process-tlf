import asyncio
import os
import asyncpg

async def main():
    db_url = "postgresql://postgres:postgres@postgres:5432/tlf_saas"
    try:
        conn = await asyncpg.connect(db_url)
        
        # Query Team
        print("\n--- Team Table ---")
        rows = await conn.fetch('SELECT * FROM "Team";')
        for r in rows:
            print(dict(r))

        # Query TeamMember
        print("\n--- TeamMember Table ---")
        rows = await conn.fetch('SELECT * FROM "TeamMember";')
        for r in rows:
            print(dict(r))

        # Query users (users table is lowercase from python backend, 
        # Stack Auth users is probably "ProjectUser" or "User")
        # Let's query information_schema to check the case of user table in stack auth
        print("\n--- User or ProjectUser ---")
        try:
            rows = await conn.fetch('SELECT * FROM "ProjectUser";')
            for r in rows:
                print(dict(r))
        except Exception as e:
            print(f"Failed: {e}")

        await conn.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == '__main__':
    asyncio.run(main())
