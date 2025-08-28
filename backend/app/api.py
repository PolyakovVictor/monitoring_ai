# backend/app/api.py
from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .db import get_session
from .models import City, Station, Pollutant, Measurement
import pandas as pd
import io
from datetime import datetime

router = APIRouter()

@router.post("/upload-csv/")
async def upload_csv(file: UploadFile, session: AsyncSession = Depends(get_session)):
    content = await file.read()
    # UHMC файли зазвичай ; та cp1251
    df = pd.read_csv(io.BytesIO(content), sep=";")

    inserted = 0

    for _, row in df.iterrows():
        print('my row: ', row)
        city_name = str(row["city"]).strip()
        station_name = str(row["coordinateNumber"]).strip()
        pollutant_name = str(row["nameImpurity"]).strip()

        # отримати або створити city
        q_city = await session.execute(select(City).where(City.name == city_name))
        city = q_city.scalar_one_or_none()
        if not city:
            city = City(name=city_name)
            session.add(city)
            await session.flush()

        # station
        q_station = await session.execute(select(Station).where(Station.name == station_name, Station.city_id == city.id))
        station = q_station.scalar_one_or_none()
        if not station:
            station = Station(name=station_name, city_id=city.id)
            session.add(station)
            await session.flush()

        # pollutant
        q_pol = await session.execute(select(Pollutant).where(Pollutant.code == pollutant_name))
        pollutant = q_pol.scalar_one_or_none()
        if not pollutant:
            pollutant = Pollutant(code=pollutant_name, description=pollutant_name)
            session.add(pollutant)
            await session.flush()

        # щоденні значення: колонки з числами 1..31
        for col in df.columns:
            if col.isdigit():
                raw_val = str(row[col]).replace(",", ".").strip()
                if raw_val in ["", "-", "nan"]:
                    continue
                try:
                    value = float(raw_val.replace("<", "").replace(">", ""))
                except ValueError:
                    continue

                # визначаємо дату
                month_year = row.get("yearMonth") if "yearMonth" in df.columns else "2025-06"
                if isinstance(month_year, str):
                    base_date = datetime.strptime(month_year, "%Y-%m")
                else:
                    base_date = datetime(2025, 6, 1)  # fallback
                day = int(col)
                m_date = datetime(base_date.year, base_date.month, day).date()

                measurement = Measurement(
                    station_id=station.id,
                    pollutant_id=pollutant.id,
                    date=m_date,
                    value=value
                )
                session.add(measurement)
                inserted += 1

    await session.commit()
    return {"rows_inserted": inserted}

