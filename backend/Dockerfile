FROM python:3.11-slim

# встановимо системні пакети
RUN apt-get update && apt-get install -y \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# poetry
ENV POETRY_VERSION=1.8.3
ENV POETRY_VIRTUALENVS_CREATE=false
RUN pip install --no-cache-dir poetry==$POETRY_VERSION

# скопіювати залежності
COPY pyproject.toml poetry.lock* ./app/

# робоча директорія
WORKDIR /app

RUN poetry install --no-root --no-interaction --no-ansi

# скопіювати код
COPY . .

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

