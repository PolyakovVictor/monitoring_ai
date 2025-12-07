import asyncio
import os
import pickle
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Measurement, Pollutant
from app.db import DATABASE_URL
from sklearn.cluster import KMeans

# Setup DB connection
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUALITY_MODEL_PATH = os.path.join(BASE_DIR, "quality_models.pkl")

async def train_quality_models():
    async with AsyncSessionLocal() as session:
        # 1. Get all pollutants
        result = await session.execute(select(Pollutant))
        pollutants = result.scalars().all()
        
        quality_models = {}
        
        print("Starting training for Air Quality Classification (K-Means)...")
        
        for p in pollutants:
            print(f"Processing {p.code}...")
            
            # 2. Get all measurements for this pollutant
            # We need a significant amount of data for clustering to make sense
            stmt = select(Measurement.value).where(Measurement.pollutant_id == p.id)
            res = await session.execute(stmt)
            values = [r for r in res.scalars().all()]
            
            if len(values) < 10:
                print(f"Skipping {p.code}: Not enough data ({len(values)} records)")
                continue
                
            # Reshape for sklearn
            X = np.array(values).reshape(-1, 1)
            
            # 3. Train K-Means
            # We want 5 clusters: Good, Moderate, Unhealthy, Very Unhealthy, Hazardous
            # If we have very few data points, reduce k
            k = 5
            if len(values) < k:
                k = len(values)
                
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X)
            
            # 4. Sort clusters
            # We need to know which cluster index corresponds to "Good" (lowest values) vs "Hazardous" (highest)
            # kmeans.cluster_centers_ is shape (k, 1)
            centroids = kmeans.cluster_centers_.flatten()
            
            # Get indices that would sort the centroids
            sorted_indices = np.argsort(centroids)
            
            # Map: sorted_rank -> original_cluster_index
            # rank 0 (lowest val) -> Good
            # rank 4 (highest val) -> Hazardous
            
            # We will store the centroids and the mapping to interpret predictions
            quality_models[p.code] = {
                "model": kmeans,
                "sorted_indices": sorted_indices, # [idx_of_min, ..., idx_of_max]
                "centroids": centroids[sorted_indices] # Sorted centroids for reference
            }
            
            print(f"  -> Trained {k} clusters. Centroids: {centroids[sorted_indices]}")

        # 5. Save models
        with open(QUALITY_MODEL_PATH, "wb") as f:
            pickle.dump(quality_models, f)
            
        print(f"Saved quality models to {QUALITY_MODEL_PATH}")

if __name__ == "__main__":
    asyncio.run(train_quality_models())
