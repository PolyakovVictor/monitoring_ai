from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import date

from .db import get_session
from .models import City, Station, Pollutant, Measurement
from .schemas import CityBase, StationBase, PollutantBase, MeasurementOut, StatsOut
from .ai import make_forecast

router = APIRouter()

# ---- 1. Міста ----
@router.get("/cities/", response_model=List[CityBase])
async def get_cities(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(City))
    return result.scalars().all()

# ---- 2. Станції у місті ----
@router.get("/cities/{city_id}/stations/", response_model=List[StationBase])
async def get_stations(city_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Station).where(Station.city_id == city_id))
    return result.scalars().all()

# ---- 3. Полютанти ----
@router.get("/pollutants/", response_model=List[PollutantBase])
async def get_pollutants(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Pollutant))
    return result.scalars().all()

# ---- 4. Вимірювання з фільтрами ----
@router.get("/measurements/", response_model=List[MeasurementOut])
async def get_measurements(
    city_id: Optional[int] = None,
    station_id: Optional[int] = None,
    pollutant_id: Optional[int] = None,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    query = (
        select(Measurement, Station, City, Pollutant)
        .join(Station, Measurement.station_id == Station.id)
        .join(City, Station.city_id == City.id)
        .join(Pollutant, Measurement.pollutant_id == Pollutant.id)
    )

    if city_id:
        query = query.where(City.id == city_id)
    if station_id:
        query = query.where(Station.id == station_id)
    if pollutant_id:
        query = query.where(Pollutant.id == pollutant_id)
    if date_from:
        query = query.where(Measurement.date >= date_from)
    if date_to:
        query = query.where(Measurement.date <= date_to)

    result = await session.execute(query)
    rows = result.all()

    return [
        MeasurementOut(
            city=city.name,
            station=station.name,
            pollutant=pollutant.code,
            date=m.date,
            value=m.value
        )
        for m, station, city, pollutant in rows
    ]

# ---- 5. Статистика ----
@router.get("/stats/", response_model=StatsOut)
async def get_stats(
    pollutant_id: int,
    city_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    session: AsyncSession = Depends(get_session),
):
    query = (
        select(
            func.avg(Measurement.value).label("avg"),
            func.min(Measurement.value).label("min"),
            func.max(Measurement.value).label("max"),
        )
        .join(Station, Measurement.station_id == Station.id)
        .join(City, Station.city_id == City.id)
        .where(Measurement.pollutant_id == pollutant_id)
    )

    if city_id:
        query = query.where(City.id == city_id)
    if date_from:
        query = query.where(Measurement.date >= date_from)
    if date_to:
        query = query.where(Measurement.date <= date_to)

    result = await session.execute(query)
    avg, min_val, max_val = result.one()

    return StatsOut(avg=avg, min=min_val, max=max_val)


@router.get("/forecast/")
async def forecast(
    city_id: int,
    date_from: date,
    date_to: date,
    session: AsyncSession = Depends(get_session),
):
    result = await make_forecast(session, city_id, date_from, date_to)
    return result
