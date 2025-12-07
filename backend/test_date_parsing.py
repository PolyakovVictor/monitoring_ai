from datetime import date
import sys
import os

# Add backend/app to path to import api
sys.path.append("/Users/morty/git/monAI/backend/app")

# Mocking imports if necessary, but let's try to import directly first
try:
    from api import parse_month_year_from_filename, parse_header_date
except ImportError:
    # If direct import fails due to relative imports in api.py (e.g. from .db), 
    # we might need to adjust sys.path or mock.
    # api.py uses 'from .db import ...', so running this script from outside the package might fail.
    # Let's try to run it as a module or just copy the functions for testing if that fails.
    print("Import failed, likely due to relative imports. Using copied functions for verification.")
    
    # Copied for verification purposes if import fails
    import re
    from datetime import datetime

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
        filename = filename.lower()
        year_match = re.search(r'20\d{2}', filename)
        year = int(year_match.group(0)) if year_match else datetime.now().year
        month = None
        for name, m_num in UA_MONTHS.items():
            if name in filename:
                month = m_num
                break
        if not month:
            month = datetime.now().month
        return year, month

    def parse_header_date(header: str, default_year: int, default_month: int):
        header = header.strip()
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
        if header.isdigit():
            day = int(header)
            try:
                return datetime(default_year, default_month, day).date()
            except ValueError:
                return None
        return None

def test_filename_parsing():
    cases = [
        ("shchodenni-za-lipen-2024.csv", (2024, 7)),
        ("shchodenni-za-traven-2024.csv", (2024, 5)),
        ("shchodenni-za-berezn-2024.csv", (2024, 3)),
        ("shchodenni-za-lipen-2025 (1).csv", (2025, 7)),
        ("shchodennisichen2024.xlsx", (2024, 1)),
        ("unknown-file.csv", (2025, 11)), # Should use current date (mocked or actual)
    ]
    
    print("Testing Filename Parsing...")
    for fname, expected in cases:
        # For unknown file, year/month depends on current date, so we skip exact assertion for it or handle it
        if fname == "unknown-file.csv":
            continue
            
        result = parse_month_year_from_filename(fname)
        if result == expected:
            print(f"[PASS] {fname} -> {result}")
        else:
            print(f"[FAIL] {fname} -> Expected {expected}, got {result}")

def test_header_parsing():
    # Context: 2024 July (7)
    year, month = 2024, 7
    
    cases = [
        ("1July", date(2024, 7, 1)),
        ("15July", date(2024, 7, 15)),
        ("1", date(2024, 7, 1)),
        ("31", date(2024, 7, 31)),
        ("32", None),
        ("city", None),
        ("coordinateNumber", None),
    ]

    print("\nTesting Header Parsing (Context: 2024-07)...")
    for header, expected in cases:
        result = parse_header_date(header, year, month)
        if result == expected:
            print(f"[PASS] {header} -> {result}")
        else:
            print(f"[FAIL] {header} -> Expected {expected}, got {result}")

    # Context: 2024 May (5) - Header has explicit month
    print("\nTesting Header Parsing (Context: 2024-05, Header: 1July)...")
    # Even if file is May, if header says July, we should probably respect header?
    # The logic says: if header has month, use it.
    result = parse_header_date("1July", 2024, 5)
    expected = date(2024, 7, 1)
    if result == expected:
        print(f"[PASS] 1July with context May -> {result}")
    else:
        print(f"[FAIL] 1July with context May -> Expected {expected}, got {result}")

if __name__ == "__main__":
    test_filename_parsing()
    test_header_parsing()
