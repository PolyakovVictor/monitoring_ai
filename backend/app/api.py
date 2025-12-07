# backend/app/api.py
from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .db import get_session
from .models import City, Station, Pollutant, Measurement
import pandas as pd
import io
from datetime import datetime

router = APIRouter()

import re

# Mapping for Ukrainian months in filenames
UA_MONTHS = {
    "sichen": 1, "siichen": 1,
    "liutii": 2, "lyutiy": 2,
    "berezn": 3, "berezne": 3,
    "kviten": 4,
    "traven": 5,
    "cherven": 6,
    "lipen": 7, "lypen": 7,
    "serpen": 8,
    "veresen": 9,
    "zhovten": 10,
    "listopad": 11, "lystopad": 11,
    "gruden": 12
}

# Mapping for English months in headers (e.g. "1July")
EN_MONTHS = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12
}

def parse_month_year_from_filename(filename: str):
    """
    Extracts month and year from filenames like:
    shchodenni-za-lipen-2024.csv
    shchodenni-za-cherven-2025 (1).csv
    shchodennisichen2024.xlsx
    """
    filename = filename.lower()
    
    # Try to find year (4 digits)
    year_match = re.search(r'20\d{2}', filename)
    year = int(year_match.group(0)) if year_match else datetime.now().year

    # Try to find month
    month = None
    for name, m_num in UA_MONTHS.items():
        if name in filename:
            month = m_num
            break
    
    # Fallback to current month if not found (or maybe raise error?)
    if not month:
        month = datetime.now().month

    return year, month

def parse_header_date(header: str, default_year: int, default_month: int):
    """
    Parses a column header to determine the date.
    Formats supported:
    1. "1July" -> Day 1, Month 7, Year default_year
    2. "1" -> Day 1, Month default_month, Year default_year
    """
    header = header.strip()
    
    # Check for "DayMonth" format (e.g. 1July)
    # Regex: starts with digits, then letters
    match = re.match(r'^(\d+)([a-zA-Z]+)$', header)
    if match:
        day_str, month_str = match.groups()
        day = int(day_str)
        month_str = month_str.lower()
        month = EN_MONTHS.get(month_str)
        if month:
            try:
                return datetime(default_year, month, day).date()
            except ValueError:
                return None

    # Check for simple number (Day)
    if header.isdigit():
        day = int(header)
        try:
            return datetime(default_year, default_month, day).date()
        except ValueError:
            return None
            
    return None


@router.post("/upload-csv/")
async def upload_csv(file: UploadFile, session: AsyncSession = Depends(get_session)):
    content = await file.read()
    filename = file.filename or ""
    
    # Extract default year/month from filename
    file_year, file_month = parse_month_year_from_filename(filename)
    
    # Detect encoding and separator
    # Priority: UTF-8 -> CP1251, Semicolon -> Comma
    encodings = ["utf-8", "cp1251"]
    separators = [";", ","]
    df = None
    
    for encoding in encodings:
        for sep in separators:
            try:
                temp_df = pd.read_csv(io.BytesIO(content), sep=sep, encoding=encoding)
                # Heuristic: Valid file should have multiple columns
                if len(temp_df.columns) > 1:
                    df = temp_df
                    break
            except Exception:
                continue
        if df is not None:
            break
            
    if df is None:
        raise HTTPException(
            status_code=400, 
            detail="Failed to parse CSV. Please ensure the file is encoded in UTF-8 or CP1251 and uses ';' or ',' as separator."
        )

    inserted = 0

    for _, row in df.iterrows():
        # Clean up basic fields
        # Using .get with defaults to avoid KeyErrors if columns are slightly different, 
        # but relying on user's schema mostly.
        city_name = str(row.get("city", "")).strip()
        station_name = str(row.get("coordinateNumber", "")).strip()
        pollutant_name = str(row.get("nameImpurity", "")).strip()
        
        if not city_name or city_name == "nan": continue
        if not station_name or station_name == "nan": continue
        if not pollutant_name or pollutant_name == "nan": continue

        # Get or create City
        q_city = await session.execute(select(City).where(City.name == city_name))
        city = q_city.scalar_one_or_none()
        if not city:
            city = City(name=city_name)
            session.add(city)
            await session.flush()

        # Get or create Station
        q_station = await session.execute(select(Station).where(Station.name == station_name, Station.city_id == city.id))
        station = q_station.scalar_one_or_none()
        if not station:
            station = Station(name=station_name, city_id=city.id)
            session.add(station)
            await session.flush()

        # Get or create Pollutant
        q_pol = await session.execute(select(Pollutant).where(Pollutant.code == pollutant_name))
        pollutant = q_pol.scalar_one_or_none()
        if not pollutant:
            pollutant = Pollutant(code=pollutant_name, description=pollutant_name)
            session.add(pollutant)
            await session.flush()

        # Iterate over columns to find date columns
        for col in df.columns:
            # Skip metadata columns
            if col in ["city", "coordinateNumber", "nameImpurity", "yearMonth"]:
                continue
                
            # Try to parse date from header
            m_date = parse_header_date(col, file_year, file_month)
            if not m_date:
                continue

            # Parse value
            raw_val = str(row[col]).replace(",", ".").strip()
            if raw_val in ["", "-", "nan", "null", "None"]:
                continue
            
            try:
                # Remove < > if present
                clean_val = raw_val.replace("<", "").replace(">", "")
                value = float(clean_val)
            except ValueError:
                continue

            # Create Measurement
            # Check if exists? For bulk upload usually we just insert. 
            # If we want to avoid duplicates, we should check. 
            # For now, let's assume we just append or the user handles cleanup.
            # Or better: check if exists to avoid PK violation if unique constraint exists.
            # Assuming no strict unique constraint on (station, pollutant, date) for now based on previous code,
            # but usually there should be one.
            
            # Let's check if measurement exists to update it or insert new
            # (Optional improvement, but good for idempotency)
            q_meas = await session.execute(select(Measurement).where(
                Measurement.station_id == station.id,
                Measurement.pollutant_id == pollutant.id,
                Measurement.date == m_date
            ))
            existing_meas = q_meas.scalar_one_or_none()
            
            if existing_meas:
                existing_meas.value = value
            else:
                measurement = Measurement(
                    station_id=station.id,
                    pollutant_id=pollutant.id,
                    date=m_date,
                    value=value
                )
                session.add(measurement)
            
            inserted += 1

    await session.commit()
    return {"rows_processed": inserted, "filename_parsed": f"{file_year}-{file_month}"}

