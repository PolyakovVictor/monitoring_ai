# backend/app/ai.py
import os
import pickle
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from .models import Measurement, Station, City, Pollutant

# Абсолютний шлях до моделі
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

async def make_forecast(session: AsyncSession, city_id: int, date_from, date_to):
    pollutants = ["PM2.5", "PM10", "NO2", "SO2", "O3", "CO"]
    features = []

    for pol in pollutants:
        q = await session.execute(
            select(func.avg(Measurement.value))
            .join(Station, Measurement.station_id == Station.id)
            .join(City, Station.city_id == City.id)
            .join(Pollutant, Measurement.pollutant_id == Pollutant.id)
            .where(City.id == city_id)
            .where(Measurement.date >= date_from)
            .where(Measurement.date <= date_to)
            .where(Pollutant.code == pol)
        )
        avg_val = q.scalar()
        features.append(avg_val or 0)

    X = np.array(features).reshape(1, -1)
    pred = model.predict(X)[0]
    return {"forecast_value": float(pred)}
x = dict().clear()