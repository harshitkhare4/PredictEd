import unittest
import os
import joblib
import pandas as pd
import numpy as np

class TestModel(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(self.base_dir, "model.pkl")
        
    def test_model_loading(self):
        """Verify model file loads successfully"""
        self.assertTrue(os.path.exists(self.model_path), f"model.pkl file not found at {self.model_path}")
        try:
            model = joblib.load(self.model_path)
            self.assertIsNotNone(model, "Model loaded as None")
        except Exception as e:
            self.fail(f"Failed to load model file: {e}")
            
    def test_model_prediction(self):
        """Verify prediction runs without errors, is numeric, and in score range"""
        self.assertTrue(os.path.exists(self.model_path), "model.pkl file not found")
        model = joblib.load(self.model_path)
        
        # Exact feature order required by the trained model
        feature_columns = [
            'Hours_Studied', 'Attendance', 'Parental_Involvement', 'Access_to_Resources',
            'Extracurricular_Activities', 'Sleep_Hours', 'Previous_Scores', 'Motivation_Level',
            'Internet_Access', 'Tutoring_Sessions', 'Family_Income', 'Teacher_Quality',
            'School_Type', 'Peer_Influence', 'Physical_Activity', 'Learning_Disabilities',
            'Parental_Education_Level', 'Distance_from_Home', 'Gender', 'Study_Efficiency',
            'Engagement'
        ]
        
        # Create single sample row using valid numerical mapping values
        sample_data = {
            'Hours_Studied': 15.0,
            'Attendance': 75.0,
            'Parental_Involvement': 1.0,  # Medium
            'Access_to_Resources': 1.0,   # Yes
            'Extracurricular_Activities': 1.0,  # Yes
            'Sleep_Hours': 7.0,
            'Previous_Scores': 75.0,
            'Motivation_Level': 1.0,      # Medium
            'Internet_Access': 1.0,       # Yes
            'Tutoring_Sessions': 2.0,
            'Family_Income': 1.0,         # Medium
            'Teacher_Quality': 1.0,       # Medium
            'School_Type': 1.0,           # Public (from Government)
            'Peer_Influence': 1.0,        # Neutral
            'Physical_Activity': 3.0,
            'Learning_Disabilities': 0.0,  # No
            'Parental_Education_Level': 1.0, # College
            'Distance_from_Home': 2.0,    # Quiet
            'Gender': 1.0,                # Male
            'Study_Efficiency': 15.0 / 7.0,
            'Engagement': 75.0
        }
        
        df = pd.DataFrame([sample_data], columns=feature_columns)
        
        try:
            prediction = model.predict(df)[0]
        except Exception as e:
            self.fail(f"Model prediction crashed: {e}")
            
        # Verify prediction output is numeric (float or int)
        self.assertTrue(isinstance(prediction, (int, float, np.integer, np.floating)), 
                        f"Prediction is not numeric: {type(prediction)}")
                        
        # Verify prediction falls within expected exam score range (0 to 100)
        self.assertTrue(0 <= prediction <= 100, 
                        f"Prediction {prediction} is out of expected score range (0-100)")

if __name__ == '__main__':
    unittest.main()
