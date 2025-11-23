import pandas as pd
import numpy as np
import glob
import pickle
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from numpy import sqrt  # Додати імпорт sqrt

def load_and_normalize(f):
    df = pd.read_csv(f, sep=";")

    # --- якщо вже є колонка date ---
    if "date" in df.columns:
        return df.rename(columns={
            "nameImpurity": "pollutant"
        })

    # --- якщо формат wide (1May, 2May, ...) ---
    id_vars = [c for c in ["city", "nameImpurity"] if c in df.columns]

    df_melted = df.melt(id_vars=id_vars, var_name="date", value_name="value")

    # парсимо дати
    def parse_date(x):
        x = str(x).strip()
        try:
            return datetime.strptime(x + "2025", "%d%b%Y").date()
        except Exception:
            try:
                return datetime.strptime(x + "2025", "%d%B%Y").date()
            except Exception:
                return None

    df_melted["date"] = df_melted["date"].apply(parse_date)
    df_melted = df_melted.dropna(subset=["date"])

    # уніфікуємо назви
    df_melted = df_melted.rename(columns={"nameImpurity": "pollutant"})

    return df_melted


# 1. Читаємо всі CSV
files = glob.glob("data/*.csv")
dfs = [load_and_normalize(f) for f in files]
data = pd.concat(dfs, ignore_index=True)

# 2. Перетворення у long (вже зробили вище)
df_long = data.copy()

# значення value в числовий формат
df_long["value"] = (
    df_long["value"]
    .astype(str)
    .str.replace(",", ".")
    .str.replace("<", "")
    .str.replace(">", "")
    .replace(["-", "nan", ""], np.nan)
    .astype(float)
)

# 3. Створюємо агреговані фічі (середні по місяцях)
df_long["month"] = pd.to_datetime(df_long["date"]).dt.to_period("M")

features = (
    df_long
    .groupby(["city", "month", "pollutant"])["value"]
    .mean()
    .reset_index()
)

features = features.pivot_table(
    index=["city", "month"],
    columns="pollutant",
    values="value"
).reset_index()

# 4. Таргет: середнє значення всіх полютантів (проксі для AQI)
features["target"] = features.drop(columns=["city", "month"]).mean(axis=1)


# 5. Модель
X = features.drop(columns=["city", "month", "target"]).fillna(0)
y = features["target"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

preds = model.predict(X_test)

# Обчислення RMSE вручну
mse = mean_squared_error(y_test, preds)
rmse = sqrt(mse)
print("RMSE:", rmse)

# 6. Збереження
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

print("✅ Модель збережена у model.pkl")
