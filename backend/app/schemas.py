# backend/app/schemas.py
from pydantic import BaseModel
from datetime import date

class MeasurementCreate(BaseModel):
    station_id: int
    pollutant_id: int
    date: date
    value: float

