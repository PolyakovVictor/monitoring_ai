import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.db import DATABASE_URL
from app.ai import get_current_air_quality_status
from app.models import City

# Setup DB connection
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def verify():
    async with AsyncSessionLocal() as session:
        # Get a city
        res = await session.execute(select(City).limit(1))
        city = res.scalars().first()
        
        if not city:
            print("No cities found in DB.")
            return

        print(f"Checking status for city: {city.name} (ID: {city.id})")
        
        status = await get_current_air_quality_status(session, city.id)
        
        print("\n--- ML-Based Status Result ---")
        print(f"Status: {status['status']}")
        print(f"Color: {status['color']}")
        print(f"Description: {status['description']}")
        print(f"Main Pollutant: {status['main_pollutant']}")
        
        if "AI analysis" in status['description']:
            print("\n✅ SUCCESS: Description confirms AI analysis is being used.")
        else:
            print("\n❌ FAILURE: Description does not mention AI analysis.")

if __name__ == "__main__":
    asyncio.run(verify())
