
import asyncio
from app.core.database import init_db, get_database

async def test_connection():
    try:
        await init_db()
        db = get_database()
        result = await db.command("ping")
        print("[OK] MongoDB connection successful!")
        print(f"   Database: {db.name}")
        
        collections = await db.list_collection_names()
        print(f"   Collections: {len(collections)}")
        for col in collections:
            count = await db[col].count_documents({})
            print(f"     - {col}: {count} documents")
        
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        exit(1)

asyncio.run(test_connection())
