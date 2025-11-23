# backend/app/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from .db import Base

class City(Base):
    __tablename__ = "cities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    lat = Column(Float)
    lng = Column(Float)

    stations = relationship("Station", back_populates="city")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user") # 'admin' or 'user'
    is_active = Column(Integer, default=1) # 1=active, 0=inactive (using int for simplicity or boolean if supported by db, assuming sqlite/postgres, int is safe)

    stations = relationship("Station", back_populates="owner")

class Station(Base):
    __tablename__ = "stations"
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String)

    city = relationship("City", back_populates="stations")
    owner = relationship("User", back_populates="stations")
    measurements = relationship("Measurement", back_populates="station")

class Pollutant(Base):
    __tablename__ = "pollutants"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    description = Column(String)

    measurements = relationship("Measurement", back_populates="pollutant")

class Measurement(Base):
    __tablename__ = "measurements"
    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id"))
    pollutant_id = Column(Integer, ForeignKey("pollutants.id"))
    date = Column(Date, index=True)
    value = Column(Float)

    station = relationship("Station", back_populates="measurements")
    pollutant = relationship("Pollutant", back_populates="measurements")

