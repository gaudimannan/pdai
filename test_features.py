import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Load data
data = pd.read_csv('data/Crop_recommendation.csv')

# 1. All Features
X_all = data[['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']]
y = data['label']
X_train, X_test, y_train, y_test = train_test_split(X_all, y, test_size=0.2, random_state=42)

model_all = RandomForestClassifier(random_state=42) # Using RF as it's usually more robust
model_all.fit(X_train, y_train)
acc_all = accuracy_score(y_test, model_all.predict(X_test))
print(f"Accuracy (All Features - N,P,K,T,H,pH,R): {acc_all:.4f}")

# 2. Weather Only
X_weather = data[['temperature', 'humidity', 'rainfall']]
X_train, X_test, y_train, y_test = train_test_split(X_weather, y, test_size=0.2, random_state=42)

model_weather = RandomForestClassifier(random_state=42)
model_weather.fit(X_train, y_train)
acc_weather = accuracy_score(y_test, model_weather.predict(X_test))
print(f"Accuracy (Weather Only - T,H,R): {acc_weather:.4f}")

# 3. Weather + pH (Maybe user can guess acidity?)
X_weather_ph = data[['temperature', 'humidity', 'rainfall', 'ph']]
X_train, X_test, y_train, y_test = train_test_split(X_weather_ph, y, test_size=0.2, random_state=42)

model_weather_ph = RandomForestClassifier(random_state=42)
model_weather_ph.fit(X_train, y_train)
acc_weather_ph = accuracy_score(y_test, model_weather_ph.predict(X_test))
print(f"Accuracy (Weather + pH): {acc_weather_ph:.4f}")
