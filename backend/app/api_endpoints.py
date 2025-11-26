from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import date

from .db import get_session
from .models import City, Station, Pollutant, Measurement, User
from .schemas import (
    CityBase, StationBase, PollutantBase, MeasurementOut, StatsOut,
    UserCreate, UserRead, Token, LoginRequest, StationCreate, StationRead
)
from .ai import make_forecast, get_current_air_quality_status
from .auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_user, get_current_admin_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from datetime import timedelta
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

router = APIRouter()

# ---- Auth ----
@router.post("/auth/register", response_model=Token)
async def register(user: UserCreate, session: AsyncSession = Depends(get_session)):
    # Check if user exists
    result = await session.execute(select(User).where(User.email == user.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    session.add(db_user)
    try:
        await session.commit()
        await session.refresh(db_user)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/login", response_model=Token)
async def login(login_data: LoginRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.email == login_data.username))
    user = result.scalars().first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# ---- Users (Admin) ----
@router.get("/users/", response_model=List[UserRead])
async def read_users(
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)
    await session.commit()
    return {"ok": True}

# ---- 1. Міста ----
@router.get("/cities/", response_model=List[CityBase])
async def get_cities(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(City))
    return result.scalars().all()

# ---- 2. Станції у місті ----
# ---- 2. Станції у місті ----
@router.get("/cities/{city_id}/stations/", response_model=List[StationRead])
async def get_stations(city_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Station).where(Station.city_id == city_id))
    return result.scalars().all()

@router.post("/stations/", response_model=StationRead)
async def create_station(
    station: StationCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    db_station = Station(**station.dict(), owner_id=current_user.id)
    session.add(db_station)
    await session.commit()
    await session.refresh(db_station)
    return db_station

@router.delete("/stations/{station_id}")
async def delete_station(
    station_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Station).where(Station.id == station_id))
    station = result.scalars().first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    
    if current_user.role != "admin" and station.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this station")
    
    await session.delete(station)
    await session.commit()
    return {"ok": True}

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


@router.get("/forecast/", response_model=List[MeasurementOut])
async def forecast(
    city_id: int,
    date_from: date,
    date_to: date,
    session: AsyncSession = Depends(get_session),
):
    result = await make_forecast(session, city_id, date_from, date_to)
    return result

@router.get("/cities/{city_id}/status")
async def get_city_status(
    city_id: int,
    session: AsyncSession = Depends(get_session),
):
    return await get_current_air_quality_status(session, city_id)
