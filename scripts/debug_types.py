import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.shared.path_manager import get_path

silver_base = get_path("storage/silver/pois_cleaned")
file_path = os.path.join(silver_base, "hanoi", "data.parquet")
df = pd.read_parquet(file_path)

print("Columns:", df.columns.tolist())
print("Dtypes:\n", df.dtypes)
print("\nSample Row Values and Types:")
for col in df.columns:
    val = df.iloc[270][col]
    print(f"{col}: {val} ({type(val)})")
