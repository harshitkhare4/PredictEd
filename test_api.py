import requests

payload = {
    "Hours_Studied": "15",
    "Attendance": "85",
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
    "School_Type": "Public",
    "Peer_Influence": "Neutral",
    "Gender": "Male"
}

print("Simulating frontend request to local Flask server...")
try:
    res = requests.post("http://127.0.0.1:5000/predict", json=payload, timeout=5)
    print(f"HTTP Status: {res.status_code}")
    print(f"JSON Output: {res.text}")
except Exception as e:
    print(f"Connection Error: {e}")
