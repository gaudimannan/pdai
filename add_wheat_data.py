import pandas as pd
import numpy as np

# Load existing data
file_path = "data/Crop_recommendation.csv"
df = pd.read_csv(file_path)

if 'wheat' in df['label'].unique():
    print("Wheat already exists. Skipping.")
else:
    print("Adding synthetic Wheat data...")
    # Generate 100 samples for Wheat
    # Temp: 10-25 C
    # Humidity: 50-70 %
    # Rainfall: 50-100 mm
    # N, P, K, pH can be generic averages as we don't use them in the simplified model,
    # but we must populate them to match CSV structure.
    
    n_samples = 150
    data = {
        'N': np.random.randint(60, 100, n_samples),
        'P': np.random.randint(30, 60, n_samples),
        'K': np.random.randint(25, 50, n_samples),
        'temperature': np.random.uniform(10, 25, n_samples),
        'humidity': np.random.uniform(50, 70, n_samples),
        'ph': np.random.uniform(6.0, 7.5, n_samples),
        'rainfall': np.random.uniform(50, 100, n_samples),
        'label': ['wheat'] * n_samples
    }
    
    wheat_df = pd.DataFrame(data)
    
    # Append to original
    df_updated = pd.concat([df, wheat_df], ignore_index=True)
    df_updated.to_csv(file_path, index=False)
    print(f"Added {n_samples} samples of Wheat. Saved to {file_path}.")
