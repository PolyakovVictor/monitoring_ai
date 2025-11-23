# backend/app/ai.py
import os
import pickle
import numpy as np
from datetime import timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Measurement, Station, City, Pollutant
from .schemas import MeasurementOut

# Absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "label_encoder.pkl")

# Load model and encoder
try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(ENCODER_PATH, "rb") as f:
        label_encoder = pickle.load(f)
except FileNotFoundError:
    model = None
    label_encoder = None
    print("⚠️ Model or Label Encoder not found. Forecasting will not work.")

async def make_forecast(session: AsyncSession, city_id: int, date_from: date, date_to: date):
    if not model or not label_encoder:
        return []

    # 1. Get all pollutants for the city (to forecast for each)
    # We only care about pollutants that actually have data in this city
    stmt = (
        select(Pollutant)
        .join(Measurement, Measurement.pollutant_id == Pollutant.id)
        .join(Station, Measurement.station_id == Station.id)
        .where(Station.city_id == city_id)
        .distinct()
    )
    result = await session.execute(stmt)
    pollutants = result.scalars().all()

    forecast_results = []
    lags = 3

    for pollutant in pollutants:
        try:
            # Check if pollutant is known to the encoder
            if pollutant.code not in label_encoder.classes_:
                continue
            
            pollutant_encoded = label_encoder.transform([pollutant.code])[0]

            # 2. Get historical data for the lags (last 3 days before date_from)
            # We need the last 'lags' measurements.
            # Note: This assumes continuous daily data. If gaps exist, this simple logic might take older data.
            # For a robust system, we should fill gaps. Here we just take the last 3 records.
            
            history_stmt = (
                select(Measurement)
                .join(Station, Measurement.station_id == Station.id)
                .where(Station.city_id == city_id)
                .where(Measurement.pollutant_id == pollutant.id)
                .where(Measurement.date < date_from)
                .order_by(Measurement.date.desc())
                .limit(lags)
            )
            history_res = await session.execute(history_stmt)
            history_measurements = history_res.scalars().all()
            
            # We need exactly 3 values. If not enough history, skip.
            if len(history_measurements) < lags:
                continue
            
            # History comes in desc order (yesterday, day before...), we need [t-1, t-2, t-3]
            # Our model was trained on [lag_1, lag_2, lag_3] where lag_1 is t-1.
            # So we need values: [val_t-1, val_t-2, val_t-3]
            
            current_lags = [m.value for m in history_measurements] # [val_t-1, val_t-2, val_t-3]
            
            # 3. Recursive Forecasting
            current_date = date_from
            while current_date <= date_to:
                # Prepare features: [pollutant_encoded, lag_1, lag_2, lag_3]
                features = np.array([pollutant_encoded] + current_lags).reshape(1, -1)
                
                # Predict
                pred_value = model.predict(features)[0]
                
                # Store result
                forecast_results.append(MeasurementOut(
                    city="", # Filled later or not needed for chart if we just use value/date
                    station="Forecast",
                    pollutant=pollutant.code,
                    date=current_date,
                    value=float(pred_value)
                ))
                
                # Update lags for next iteration
                # New lag_1 is the prediction
                # New lag_2 is old lag_1
                # New lag_3 is old lag_2
                current_lags = [pred_value] + current_lags[:-1]
                
                current_date += timedelta(days=1)
                
        except Exception as e:
            print(f"Error forecasting for {pollutant.code}: {e}")
            continue

    return forecast_results