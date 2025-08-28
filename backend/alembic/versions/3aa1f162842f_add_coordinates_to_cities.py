"""Add coordinates to cities

Revision ID: 3aa1f162842f
Revises: 95540a08420e
Create Date: 2025-08-28 16:20:16.352102

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sqlalchemy.sql import table, column
from sqlalchemy import String, Float

# revision identifiers, used by Alembic.
revision: str = '3aa1f162842f'
down_revision: Union[str, Sequence[str], None] = '95540a08420e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Створюємо тимчасову таблицю cities
cities_table = table('cities',
    column('id', String),
    column('lat', Float),
    column('lng', Float)
)

# Дані координат
city_coords = {
    1: (50.4501, 30.5234),   # Київ
    2: (49.2328, 28.4800),   # Вінниця
    3: (50.7472, 25.3254),   # Луцьк
    4: (48.6208, 22.2879),   # Ужгород
    5: (47.8388, 35.1396),   # Запоріжжя
    6: (48.9226, 24.7103),   # Івано-Франківськ
    7: (48.4647, 35.0462),   # Дніпро
    8: (47.9105, 33.3918),   # Кривий Ріг
    9: (48.5216, 34.6044),   # Кам'янське
    10: (48.5070, 32.2623),  # Кропивницький
    11: (49.0486, 33.2414),  # Світловодськ
    12: (49.8397, 24.0297),  # Львів
    13: (46.9750, 31.9946),  # Миколаїв
    14: (46.4825, 30.7233),  # Одеса
    15: (49.5883, 34.5514),  # Полтава
    16: (49.0675, 33.4160),  # Кременчук
    17: (50.6199, 26.2516),  # Рівне
    18: (50.9077, 34.7981),  # Суми
    19: (49.5535, 25.5948),  # Тернопіль
    20: (49.9935, 36.2304),  # Харків
    21: (49.4216, 26.9965),  # Хмельницький
    22: (46.6354, 32.6169),  # Херсон
    23: (49.4444, 32.0598),  # Черкаси
    24: (48.2915, 25.9403),  # Чернівці
    25: (45.3499, 28.8370),  # Ізмаїл
    26: (49.8059, 30.1153),  # Біла Церква
    27: (48.6690, 33.1171),  # Олександрія
    28: (49.3599, 33.5186),  # Горішні Плавні
    29: (50.5181, 30.8030),  # Бровари
    30: (50.1071, 30.6220),  # Обухів
    31: (50.1472, 30.7399),  # Українка
    32: (50.2547, 28.6587),  # Житомир
    33: (51.4982, 31.2893),  # Чернігів
}

def upgrade():
    for city_id, (lat, lng) in city_coords.items():
        op.execute(
            cities_table.update().where(cities_table.c.id == city_id).values(lat=lat, lng=lng)
        )


def downgrade() -> None:
    """Downgrade schema."""
    pass
