import pandas as pd
import numpy as np
import glob
import pickle
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import LabelEncoder
from math import sqrt

def load_and_normalize(f):
    df = pd.read_csv(f, sep=";")

    # --- if date column exists ---
    if "date" in df.columns:
        return df.rename(columns={
            "nameImpurity": "pollutant"
        })

    # --- if wide format (1May, 2May, ...) ---
    id_vars = [c for c in ["city", "nameImpurity"] if c in df.columns]

    df_melted = df.melt(id_vars=id_vars, var_name="date", value_name="value")

    # parse dates
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

    # unify names
    df_melted = df_melted.rename(columns={"nameImpurity": "pollutant"})

    return df_melted


# 1. Read all CSVs
files = glob.glob("data/*.csv")
dfs = [load_and_normalize(f) for f in files]
data = pd.concat(dfs, ignore_index=True)

# 2. Clean values
df_long = data.copy()
df_long["value"] = (
    df_long["value"]
    .astype(str)
    .str.replace(",", ".")
    .str.replace("<", "")
    .str.replace(">", "")
    .replace(["-", "nan", ""], np.nan)
    .astype(float)
)
df_long = df_long.dropna(subset=["value"])

# 3. Sort by date
df_long = df_long.sort_values(["city", "pollutant", "date"])

# 4. Create Lagged Features
# We want to predict value_t using value_t-1, value_t-2, value_t-3
lags = 3
for lag in range(1, lags + 1):
    df_long[f"lag_{lag}"] = df_long.groupby(["city", "pollutant"])["value"].shift(lag)

df_long = df_long.dropna()

# 5. Encode Pollutant
le = LabelEncoder()
df_long["pollutant_encoded"] = le.fit_transform(df_long["pollutant"])

# Save the encoder for inference
with open("label_encoder.pkl", "wb") as f:
    pickle.dump(le, f)

# 6. Prepare Features and Target
feature_cols = ["pollutant_encoded"] + [f"lag_{i}" for i in range(1, lags + 1)]
X = df_long[feature_cols]
y = df_long["value"]

print(f"Training on {len(X)} samples with features: {feature_cols}")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 7. Train Model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

preds = model.predict(X_test)
rmse = sqrt(mean_squared_error(y_test, preds))
print("RMSE:", rmse)

# 8. Save Model
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

print("✅ Model saved to model.pkl")
print("✅ Label Encoder saved to label_encoder.pkl")
