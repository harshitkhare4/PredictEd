# PredictEd – AI-Based Academic Performance Analysis System

PredictEd is a Machine Learning powered web application designed to predict student academic performance using behavioral and academic attributes.

The system uses a Random Forest Regression model trained on student-related factors such as:
- Study Hours
- Attendance
- Motivation Level
- Previous Scores
- Sleep Hours
- Study Environment
- Internet Access
- Teacher Quality
- Peer Influence

---

## Features

- AI-based exam score prediction
- Dynamic performance analysis
- Feature importance visualization
- PostgreSQL model storage support
- Random Forest Regression
- Interactive modern UI
- Loading screen for Render cold starts
- Production-ready Flask backend

---

## Tech Stack

### Frontend
- HTML
- CSS
- JavaScript

### Backend
- Flask
- Gunicorn

### Machine Learning
- Scikit-learn
- Random Forest Regression
- NumPy
- Pandas
- Joblib

### Database
- PostgreSQL
- psycopg2

### Deployment
- Render
- GitHub

---

## Machine Learning Workflow

1. User enters academic and behavioral data
2. Frontend sends request to Flask API
3. Backend preprocesses inputs
4. Random Forest model predicts exam score
5. Dynamic academic analysis is generated
6. Feature importance data is visualized

---

## Prediction Categories

### Performance Levels
- Poor
- Average
- Good
- Excellent

### Dynamic Academic Analysis
The application generates performance explanations dynamically based on predicted score ranges.

---

## Database Integration

The trained ML model can be:
- Loaded from PostgreSQL BYTEA storage
- Loaded from local model.pkl fallback
- Automatically verified during startup

---

## Deployment Notes

Render free instances may take time during cold starts.  
A professional loading screen is implemented to improve user experience during initialization.

---

Harshit Khare
B.Tech CSE (AI & ML)

Live Demo

https://predicted-ai.onrender.com