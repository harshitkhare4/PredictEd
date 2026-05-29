import os
import joblib
import sys
import sklearn
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, render_template
from db import init_connection_pool
from model_utils import init_db, save_model_to_db, load_model_from_db

import site

app = Flask(__name__)

print("="*40)
print("PREDICTED ML ENGINE ENVIRONMENT CHECK")
print(f"Active Python Interpreter: {sys.executable}")
print(f"Python Version: {sys.version.split(' ')[0]}")
if hasattr(site, 'getsitepackages'):
    print(f"Site Packages path: {site.getsitepackages()}")
print("="*40)

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")

# Global variables for model and feature importances
model = None
feature_importances = {}
model_error = "Model not initialized"
MODEL_SOURCE = "unknown"

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

# Initialize DB on startup (safely attempts, ignores if no DATABASE_URL)
try:
    init_db()
except Exception as e:
    print(f"PostgreSQL not initialized: {e}")

def get_model():
    global model, feature_importances, model_error, MODEL_SOURCE
    
    # Return from cache if already loaded
    if model is not None:
        return model
        
    model_error = None
    
    print("="*40)
    print("PREDICTED ML ENGINE LAZY STARTUP")
    print(f"Python version: {sys.version.split(' ')[0]}")
    print(f"Scikit-Learn version: {sklearn.__version__}")
    print("="*40)
    
    # Strategy 1: Attempt to load from local filesystem (Fastest for local dev)
    print(f"[Hybrid Load] Attempting local filesystem load from {MODEL_PATH}...")
    if os.path.exists(MODEL_PATH):
        try:
            model = joblib.load(MODEL_PATH)
            MODEL_SOURCE = "local_file"
            print("[Hybrid Load] SUCCESS: Model loaded from local filesystem.")
        except Exception as e:
            print(f"[Hybrid Load] Failed to load local model: {e}")
            model = None
    else:
        print(f"[Hybrid Load] Local model file not found at {MODEL_PATH}")

    # Strategy 2: Fallback to PostgreSQL (Deployment safe)
    if model is None:
        print("[Hybrid Load] Attempting PostgreSQL fallback load...")
        try:
            model = load_model_from_db()
            if model:
                MODEL_SOURCE = "postgresql"
                print("[Hybrid Load] SUCCESS: Model loaded from PostgreSQL.")
            else:
                model_error = "Model not found in PostgreSQL and local file missing."
                print(f"ERROR: {model_error}")
        except Exception as db_err:
            print(f"[Hybrid Load] Failed to load from PostgreSQL: {db_err}")
            model_error = str(db_err)

    # Strategy 3: Setup globals if load was successful
    if model is not None:
        try:
            if hasattr(model, 'feature_importances_'):
                importances = dict(zip(FEATURE_COLUMNS, model.feature_importances_))
                feature_importances = sorted(importances.items(), key=lambda x: x[1], reverse=True)
        except Exception as feat_err:
            print(f"Failed to parse feature importances: {feat_err}")
            
        print("Hybrid Model Loading Complete. Engine ready for predictions!")
        return model
        
    print("CRITICAL ERROR: Hybrid model loading failed completely.")
    return None



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

@app.route('/predict', methods=['POST'])
def predict():
    try:
        current_model = get_model()
        print(f"--- MODEL LOADED STATUS: {'SUCCESS' if current_model is not None else 'FAILED'} ---")
        if current_model is None:
            return jsonify({'success': False, 'error': f"Model failed to load: {model_error}"}), 500
            
        data = request.json
        print("--- INCOMING PREDICTION REQUEST ---")
        print(f"Received input: {data}")
        
        if not data:
            return jsonify({'success': False, 'error': 'No input data provided'}), 400
            
        # Copy input data so we don't modify request JSON in-place
        processed_data = data.copy()
        
        # Map Institution_Type -> School_Type (Government -> Public, Private -> Private)
        if 'Institution_Type' in processed_data:
            inst_val = processed_data['Institution_Type']
            if inst_val == 'Government':
                processed_data['School_Type'] = 'Public'
            elif inst_val == 'Private':
                processed_data['School_Type'] = 'Private'
        
        # Prepare feature mapping dictionary
        mapped_features = {}
        
        # 1. Map all continuous numerical inputs directly
        try:
            mapped_features['Hours_Studied'] = float(processed_data.get('Hours_Studied', 15.0))
            mapped_features['Attendance'] = float(processed_data.get('Attendance', 75.0))
            mapped_features['Sleep_Hours'] = float(processed_data.get('Sleep_Hours', 7.0))
            
            prev_scores = float(processed_data.get('Previous_Scores', 75.0))
            if prev_scores < 0 or prev_scores > 100:
                return jsonify({'error': 'Previous Exam Score must be between 0 and 100 inclusive.'}), 400
            mapped_features['Previous_Scores'] = prev_scores
            
            mapped_features['Tutoring_Sessions'] = float(processed_data.get('Tutoring_Sessions', 2.0))
            mapped_features['Physical_Activity'] = float(processed_data.get('Physical_Activity', 3.0))
        except ValueError as val_err:
            return jsonify({'error': f'Invalid numerical input: {str(val_err)}'}), 400
            
        # 2. Map categorical fields using our reverse-engineered mappings
        for field, mapping in CATEGORICAL_MAPPINGS.items():
            user_val = processed_data.get(field)
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
            raw_score = current_model.predict(df)[0]
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

@app.route('/feature-importance', methods=['GET'])
def get_feature_info():
    """
    API endpoint that safely extracts Random Forest feature importances 
    without crashing if metadata is stripped in production.
    """
    try:
        print(f"--- ROUTE HIT: /feature-importance ---")
        current_model = get_model()
        print(f"Model Source: {MODEL_SOURCE}")
        
        if current_model is None or not feature_importances:
            print("Feature importance extraction failed or model unavailable.")
            return jsonify({'success': False, 'error': f'Feature importance unavailable: {model_error}'})
            
        # Validate safety check requested by user
        if not hasattr(current_model, "feature_importances_"):
            print("Model lacks feature_importances_ attribute.")
            return jsonify({'success': False, 'error': 'Model metadata stripped.'})
            
        print("Feature importance extracted successfully.")
        
        features = [name.replace('_', ' ') for name, val in feature_importances]
        importance_vals = [round(float(val) * 100, 2) for name, val in feature_importances]
        
        return jsonify({
            'success': True,
            'features': features,
            'importance': importance_vals
        })
    except Exception as e:
        print(f"Feature Importance Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/save-model', methods=['POST'])
def save_model_api():
    try:
        if not os.path.exists(MODEL_PATH):
            return jsonify({'success': False, 'error': 'Local model.pkl not found to save.'}), 404
            
        success = save_model_to_db(MODEL_PATH)
        if success:
            return jsonify({'success': True, 'message': 'Model successfully uploaded to PostgreSQL.'})
        else:
            return jsonify({'success': False, 'error': 'Failed to save model to PostgreSQL. Check server logs.'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/model-source', methods=['GET'])
def get_model_source():
    try:
        # Force a lazy load if it hasn't happened yet
        get_model()
        return jsonify({
            "success": True,
            "model_source": MODEL_SOURCE,
            "model_loaded": model is not None,
            "error": model_error if model is None else None
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Do not call load_model() here anymore. It will lazy-load on the first request!
    app.run(host='0.0.0.0', port=5000, debug=True)
