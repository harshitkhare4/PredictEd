import unittest
import json
from app import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()
        
    def test_health_check(self):
        """Verify health endpoint returns 200 and correct status JSON"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, {"status": "healthy"})
        
    def test_predict_endpoint_success(self):
        """Verify predict endpoint returns 200 with valid input"""
        payload = {
            "Hours_Studied": "15",
            "Attendance": "75",
            "Previous_Scores": "75",
            "Tutoring_Sessions": "2",
            "Motivation_Level": "Medium",
            "Teacher_Quality": "Medium",
            "Sleep_Hours": "7",
            "Physical_Activity": "3",
            "Distance_from_Home": "Quiet",
            "Extracurricular_Activities": "Yes",
            "Access_to_Resources": "Yes",
            "Internet_Access": "Yes",
            "Learning_Disabilities": "No",
            "Family_Income": "Medium",
            "Parental_Involvement": "Medium",
            "Parental_Education_Level": "College",
            "Institution_Type": "Government", # maps to Public
            "Peer_Influence": "Neutral",
            "Gender": "Male"
        }
        response = self.client.post('/predict', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data.get('success'), f"Prediction API returned success=False: {data}")
        self.assertIn('exam_score', data)
        self.assertIn('performance_level', data)
        self.assertTrue(isinstance(data['exam_score'], (int, float)))
        self.assertTrue(0 <= data['exam_score'] <= 100)
        
    def test_predict_invalid_payload(self):
        """Verify invalid payload returns proper error (e.g. invalid type or values)"""
        # Case 1: Bad categorical value (Motivation_Level is invalid)
        payload = {
            "Hours_Studied": "15",
            "Attendance": "75",
            "Previous_Scores": "75",
            "Tutoring_Sessions": "2",
            "Motivation_Level": "SuperHigh", # Invalid
            "Teacher_Quality": "Medium",
            "Sleep_Hours": "7",
            "Physical_Activity": "3",
            "Distance_from_Home": "Quiet",
            "Extracurricular_Activities": "Yes",
            "Access_to_Resources": "Yes",
            "Internet_Access": "Yes",
            "Learning_Disabilities": "No",
            "Family_Income": "Medium",
            "Parental_Involvement": "Medium",
            "Parental_Education_Level": "College",
            "Institution_Type": "Government",
            "Peer_Influence": "Neutral",
            "Gender": "Male"
        }
        response = self.client.post('/predict', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        
    def test_predict_missing_fields(self):
        """Verify missing fields are handled safely and return an informative client error"""
        payload = {
            "Hours_Studied": "15",
            "Attendance": "75"
            # Missing most fields
        }
        response = self.client.post('/predict', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()
