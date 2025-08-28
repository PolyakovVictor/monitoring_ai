# backend/app/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from .db import Base

class City(Base):
    __tablename__ = "cities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    stations = relationship("Station", back_populates="city")

class Station(Base):
    __tablename__ = "stations"
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"))
    name = Column(String)

    city = relationship("City", back_populates="stations")
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

