import os
import joblib
import sys
import sklearn
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")

# Global variables for model and feature importances
model = None
feature_importances = {}
model_error = "Model not initialized"

# Mappings for categorical/binary columns
CATEGORICAL_MAPPINGS = {
    'Parental_Involvement': {'Low': 0, 'Medium': 1, 'High': 2},
    'Motivation_Level': {'Low': 0, 'Medium': 1, 'High': 2},
    'Family_Income': {'Low': 0, 'Medium': 1, 'High': 2},
    'Teacher_Quality': {'Low': 0, 'Medium': 1, 'High': 2},
    'Peer_Influence': {'Negative': 0, 'Neutral': 1, 'Positive': 2},
    'Distance_from_Home': {'Distracting': 0, 'Average': 1, 'Quiet': 2},
    'Parental_Education_Level': {'College': 0, 'High School': 1, 'Postgraduate': 2},
    'School_Type': {'Private': 0, 'Public': 1},
    'Internet_Access': {'No': 0, 'Yes': 1},
    'Extracurricular_Activities': {'No': 0, 'Yes': 1},
    'Learning_Disabilities': {'No': 0, 'Yes': 1},
    'Access_to_Resources': {'No': 0, 'Yes': 1},
    'Gender': {'Female': 0, 'Male': 1}
}

# Exact feature order required by the trained model (Fixes Render sklearn metadata deployment bug)
FEATURE_COLUMNS = [
    'Hours_Studied', 'Attendance', 'Parental_Involvement', 'Access_to_Resources',
    'Extracurricular_Activities', 'Sleep_Hours', 'Previous_Scores', 'Motivation_Level',
    'Internet_Access', 'Tutoring_Sessions', 'Family_Income', 'Teacher_Quality',
    'School_Type', 'Peer_Influence', 'Physical_Activity', 'Learning_Disabilities',
    'Parental_Education_Level', 'Distance_from_Home', 'Gender', 'Study_Efficiency',
    'Engagement'
]

def load_model():
    global model, feature_importances, model_error
    model_error = None
    
    print("="*40)
    print("PREDICTED ML ENGINE STARTUP")
    print(f"Python version: {sys.version.split(' ')[0]}")
    print(f"Scikit-Learn version: {sklearn.__version__}")
    print("="*40)
    
    print(f"🔍 BASE_DIR Detected: {BASE_DIR}")
    print(f"🔍 Expected MODEL_PATH: {MODEL_PATH}")
    
    try:
        print(f"📂 Directory contents of BASE_DIR: {os.listdir(BASE_DIR)}")
    except Exception as list_err:
        print(f"⚠️ Failed to list directory contents: {list_err}")
    
    if not os.path.exists(MODEL_PATH):
        model_error = f"Model file NOT FOUND at: {MODEL_PATH}"
        print(f"ERROR: {model_error}")
        return
    
    print(f"Loading ML model from {MODEL_PATH}...")
    try:
        model = joblib.load(MODEL_PATH)
        
        if hasattr(model, 'feature_names_in_'):
            print("Model Expected Features:")
            print(list(model.feature_names_in_))
        else:
            print("WARNING: model.feature_names_in_ is NOT available on this model.")
        
        # Store feature importances for use in the About page API (safely without feature_names_in_)
        if hasattr(model, 'feature_importances_'):
            importances = dict(zip(FEATURE_COLUMNS, model.feature_importances_))
            # Sort them descending
            feature_importances = sorted(importances.items(), key=lambda x: x[1], reverse=True)
            
        print("Model loaded successfully and is ready for predictions!")
    except Exception as e:
        model_error = str(e)
        print(f"CRITICAL ERROR: Failed to load model from {MODEL_PATH}")
        print(f"Exception details: {model_error}")
        import traceback
        traceback.print_exc()
        model = None



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        print(f"--- MODEL LOADED STATUS: {'SUCCESS' if model is not None else 'FAILED'} ---")
        if model is None:
            return jsonify({'success': False, 'error': f"Model failed to load: {model_error}"}), 500
            
        data = request.json
        print("--- INCOMING PREDICTION REQUEST ---")
        print(f"Received input: {data}")
        
        if not data:
            return jsonify({'success': False, 'error': 'No input data provided'}), 400
        
        # Prepare feature mapping dictionary
        mapped_features = {}
        
        # 1. Map all continuous numerical inputs directly
        try:
            mapped_features['Hours_Studied'] = float(data.get('Hours_Studied', 15.0))
            mapped_features['Attendance'] = float(data.get('Attendance', 85.0))
            mapped_features['Sleep_Hours'] = float(data.get('Sleep_Hours', 7.0))
            mapped_features['Previous_Scores'] = float(data.get('Previous_Scores', 75.0))
            mapped_features['Tutoring_Sessions'] = float(data.get('Tutoring_Sessions', 2.0))
            mapped_features['Physical_Activity'] = float(data.get('Physical_Activity', 3.0))
        except ValueError as val_err:
            return jsonify({'error': f'Invalid numerical input: {str(val_err)}'}), 400
            
        # 2. Map categorical fields using our reverse-engineered mappings
        for field, mapping in CATEGORICAL_MAPPINGS.items():
            user_val = data.get(field)
            if user_val not in mapping:
                return jsonify({'error': f"Invalid or missing value for field '{field}': '{user_val}'. Valid values: {list(mapping.keys())}"}), 400
            mapped_features[field] = float(mapping[user_val])
            
        # 3. Dynamic Feature Engineering (Calculated in backend)
        # Study_Efficiency = Hours_Studied / Sleep_Hours
        if mapped_features['Sleep_Hours'] == 0:
            return jsonify({'error': 'Sleep Hours cannot be zero.'}), 400
            
        mapped_features['Study_Efficiency'] = mapped_features['Hours_Studied'] / mapped_features['Sleep_Hours']
        
        # Engagement = Attendance
        mapped_features['Engagement'] = mapped_features['Attendance']
        
        # Create DataFrame in correct column order expected by model using hardcoded array
        df = pd.DataFrame([mapped_features], columns=FEATURE_COLUMNS)
        
        print("--- DATAFRAME GENERATED ---")
        print(f"Columns: {list(df.columns)}")
        print(f"Shape: {df.shape}")
        if hasattr(model, 'feature_names_in_'):
            print(f"Model Expected: {list(model.feature_names_in_)}")
        
        # Run prediction safely
        try:
            raw_score = model.predict(df)[0]
        except Exception as pred_err:
            print(f"Core Prediction Engine Error: {str(pred_err)}")
            return jsonify({'success': False, 'error': f"sklearn prediction failed: {str(pred_err)}"}), 500
            
        exam_score = round(float(raw_score), 2)
        
        # Determine Performance Level
        if exam_score >= 80:
            performance_level = "Excellent"
        elif exam_score >= 60:
            performance_level = "Good"
        elif exam_score >= 40:
            performance_level = "Average"
        else:
            performance_level = "Poor"
            
        print(f"Prediction generated: Score={exam_score}, Level={performance_level}")
            
        return jsonify({
            'success': True,
            'exam_score': exam_score,
            'performance_level': performance_level,
            'attendance_status': f"{mapped_features['Attendance']}%",
            'engagement_level': round(mapped_features['Engagement'], 2)
        })
        
    except Exception as e:
        print(f"Prediction Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Prediction failed: {str(e)}'}), 500

@app.route('/about-features', methods=['GET'])
def get_feature_info():
    """
    Returns feature importances extracted directly from the RandomForestRegressor.
    This creates an extremely smart 'About' or 'Features' page.
    """
    try:
        if model is None or not feature_importances:
            return jsonify({'success': False, 'error': f'Feature importance unavailable: {model_error}'})
            
        importances_list = [{'feature': name.replace('_', ' '), 'importance': round(float(val) * 100, 2)} for name, val in feature_importances]
        return jsonify({
            'success': True,
            'importances': importances_list
        })
    except Exception as e:
        print(f"Feature Importance Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize model before starting the server
    load_model()
    
    # Start Flask Server
    app.run(host='0.0.0.0', port=5000, debug=True)
