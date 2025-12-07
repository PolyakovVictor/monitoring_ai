# backend/app/schemas.py
from pydantic import BaseModel
from datetime import date
from typing import Optional, List


class MeasurementCreate(BaseModel):
    station_id: int
    pollutant_id: int
    date: date
    value: float


# ---- City ----
class CityBase(BaseModel):
    id: int
    name: str
    lat: Optional[float] = None
    lng: Optional[float] = None

    class Config:
        orm_mode = True

# ---- Station ----
class StationBase(BaseModel):
    id: int
    name: str
    city_id: int

    class Config:
        orm_mode = True

# ---- Pollutant ----
class PollutantBase(BaseModel):
    id: int
    code: str
    description: Optional[str] = None

    class Config:
        orm_mode = True

# ---- Measurement ----
class MeasurementBase(BaseModel):
    id: int
    station_id: int
    pollutant_id: int
    date: date
    value: float

    class Config:
        orm_mode = True

# ---- Measurement with joins ----
class MeasurementOut(BaseModel):
    city: str
    station: str
    pollutant: str
    date: date
    value: float

# ---- Stats ----
class StatsOut(BaseModel):
    avg: Optional[float]
    min: Optional[float]
    max: Optional[float]

# ---- Auth & Users ----
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    role: str
    is_active: int

    class Config:
        orm_mode = True

class LoginRequest(BaseModel):
    username: str # OAuth2PasswordRequestForm uses username, but we can support email here too if we want custom login endpoint
    password: str

# ---- Station Update ----
class StationCreate(BaseModel):
    name: str
    city_id: int

class StationRead(StationBase):
    owner_id: Optional[int] = None

# ---- Report ----
class PollutantStats(BaseModel):
    pollutant: str
    avg: Optional[float]
    min: Optional[float]
    max: Optional[float]

class ReportOut(BaseModel):
    city: str
    date: date
    status: dict # Reusing the status dict structure
    stats: List[PollutantStats]


