import pandas as pd
import numpy as np

# Load existing data
file_path = "data/Crop_recommendation.csv"
df = pd.read_csv(file_path)

# New Crops to Add
new_crops = {
    'wheat': {
        'temp': (10, 25), 'humid': (50, 70), 'rain': (50, 100), 'ph': (6.0, 7.5)
    },
    'potato': {
        'temp': (15, 25), 'humid': (60, 80), 'rain': (50, 100), 'ph': (5.0, 6.5)
    },
    'sugarcane': {
        'temp': (25, 35), 'humid': (80, 95), 'rain': (150, 250), 'ph': (6.0, 7.5)
    },
    'soybean': {
        'temp': (20, 32), 'humid': (60, 80), 'rain': (90, 160), 'ph': (6.0, 7.0)
    },
    'oilseeds': { # Modeling as Mustard/Rapeseed
        'temp': (15, 25), 'humid': (45, 65), 'rain': (30, 70), 'ph': (6.0, 7.5)
    }
}

dfs_to_add = []
n_samples = 150

for crop, params in new_crops.items():
    if crop in df['label'].unique():
        print(f"{crop} already exists. Skipping.")
        continue
        
    print(f"Generating data for {crop}...")
    data = {
        'N': np.random.randint(40, 120, n_samples), # Generic ranges
        'P': np.random.randint(30, 70, n_samples),
        'K': np.random.randint(30, 60, n_samples),
        'temperature': np.random.uniform(params['temp'][0], params['temp'][1], n_samples),
        'humidity': np.random.uniform(params['humid'][0], params['humid'][1], n_samples),
        'ph': np.random.uniform(params['ph'][0], params['ph'][1], n_samples),
        'rainfall': np.random.uniform(params['rain'][0], params['rain'][1], n_samples),
        'label': [crop] * n_samples
    }
    dfs_to_add.append(pd.DataFrame(data))

if dfs_to_add:
    df_updated = pd.concat([df] + dfs_to_add, ignore_index=True)
    df_updated.to_csv(file_path, index=False)
    print(f"Added {len(dfs_to_add)} new crops. Saved to {file_path}.")
else:
    print("No new crops added.")
