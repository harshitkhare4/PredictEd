import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

FEATURE_COLUMNS = [
    'Hours_Studied', 'Attendance', 'Parental_Involvement', 'Access_to_Resources',
    'Extracurricular_Activities', 'Sleep_Hours', 'Previous_Scores', 'Motivation_Level',
    'Internet_Access', 'Tutoring_Sessions', 'Family_Income', 'Teacher_Quality',
    'School_Type', 'Peer_Influence', 'Physical_Activity', 'Learning_Disabilities',
    'Parental_Education_Level', 'Distance_from_Home', 'Gender', 'Study_Efficiency',
    'Engagement'
]

# Generate synthetic academic data
np.random.seed(42)
n_samples = 1000

data = {
    'Hours_Studied': np.random.uniform(5, 30, n_samples),
    'Attendance': np.random.uniform(60, 100, n_samples),
    'Parental_Involvement': np.random.choice([0, 1, 2], n_samples), # Low, Medium, High
    'Access_to_Resources': np.random.choice([0, 1], n_samples), # No, Yes
    'Extracurricular_Activities': np.random.choice([0, 1], n_samples),
    'Sleep_Hours': np.random.uniform(4, 10, n_samples),
    'Previous_Scores': np.random.uniform(50, 100, n_samples),
    'Motivation_Level': np.random.choice([0, 1, 2], n_samples),
    'Internet_Access': np.random.choice([0, 1], n_samples),
    'Tutoring_Sessions': np.random.uniform(0, 5, n_samples),
    'Family_Income': np.random.choice([0, 1, 2], n_samples),
    'Teacher_Quality': np.random.choice([0, 1, 2], n_samples),
    'School_Type': np.random.choice([0, 1], n_samples),
    'Peer_Influence': np.random.choice([0, 1, 2], n_samples),
    'Physical_Activity': np.random.uniform(0, 7, n_samples),
    'Learning_Disabilities': np.random.choice([0, 1], n_samples),
    'Parental_Education_Level': np.random.choice([0, 1, 2], n_samples),
    'Distance_from_Home': np.random.choice([0, 1, 2], n_samples), # 0: Distracting, 1: Avg, 2: Quiet
    'Gender': np.random.choice([0, 1], n_samples)
}

# Calculated features
data['Study_Efficiency'] = data['Hours_Studied'] / np.maximum(data['Sleep_Hours'], 1)
data['Engagement'] = data['Attendance']

df = pd.DataFrame(data)

# Ensure exact column order
df = df[FEATURE_COLUMNS]

# Generate a target variable (Exam Score) based on weights ensuring logical predictions
target = (
    df['Hours_Studied'] * 1.5 + 
    df['Attendance'] * 0.4 + 
    df['Previous_Scores'] * 0.3 + 
    df['Motivation_Level'] * 3 +
    df['Access_to_Resources'] * 2 +
    df['Sleep_Hours'] * 1.2 +
    df['Distance_from_Home'] * 2.5 + # Quiet environments yield higher scores
    np.random.normal(0, 4, n_samples)
)
# Bound target to standard academic grading 0-100
target = np.clip(target, 0, 100)

print("Training Random Forest Regressor (sklearn 1.4.2)...")
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(df, target)

print("Saving model via joblib...")
joblib.dump(model, "model.pkl")

print("\n--- DEPLOYMENT VERIFICATION ---")
loaded_model = joblib.load("model.pkl")

print("1. Testing prediction...")
test_input = pd.DataFrame([df.iloc[0]])
pred = loaded_model.predict(test_input)[0]
print(f"Predicted Score: {pred:.2f} (Actual label: {target[0]:.2f})")

print("2. Testing feature importances...")
if hasattr(loaded_model, 'feature_importances_'):
    print("SUCCESS: feature_importances_ is available and attached!")
    importances = dict(zip(FEATURE_COLUMNS, loaded_model.feature_importances_))
    top_3 = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:3]
    print(f"Top 3 driving features: {top_3}")
else:
    print("CRITICAL ERROR: feature_importances_ not found.")

print("\nModel rebuild complete! Ready for Render deployment.")
