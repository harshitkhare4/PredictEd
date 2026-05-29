# PredictEd – Complete Production Deployment & Safe Git Workflow Guide

Welcome to the production guide for **PredictEd**, an AI-based Academic Performance Analysis System. This document serves as the single source of truth for establishing a bulletproof, production-grade deployment architecture where no code can be merged or deployed unless all validation and automated test suites pass successfully.

---

## 🏗️ 1. Local Environment Setup

To run PredictEd locally and execute the automated test suites, set up a dedicated Python environment:

1. **Clone the Repository**:
   ```bash
   git clone <your-repository-url>
   cd Performance-tracker
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment**:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt)**:
     ```cmd
     .\venv\Scripts\activate.bat
     ```
   - **macOS / Linux**:
     ```bash
     source venv/bin/activate
     ```

4. **Install Dependencies**:
   Install core packages alongside testing utilities (`pytest` and `flake8`):
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install pytest flake8
   ```

---

## 🧪 2. Running Automated Tests Locally

Before making commits, opening Pull Requests, or recommending deployment, you **MUST** run all automated tests locally.

### Executing the Entire Test Suite
Run the test suites using standard Python `unittest`:
```bash
python -m unittest test_model.py test_api.py
```

Or using `pytest` for highly detailed, colorized output:
```bash
pytest test_model.py test_api.py -v
```

### What These Tests Verify:
1. **Model Loading & Inference Integrity (`test_model.py`)**:
   - Assures that `model.pkl` exists and is successfully deserialized using `joblib`.
   - Confirms that prediction executes without crashing, taking feature inputs in the exact schema order expected by the model.
   - Validates that the prediction score output is a float or integer and falls within the logical bounds of an exam score (`0` to `100`).

2. **Backend API Endpoints (`test_api.py`)**:
   - **GET `/health`**: Asserts it returns status code `200` and `{"status": "healthy"}`.
   - **POST `/predict` Success**: Submits a valid student profile with the new `Institution_Type` and `Peer_Influence` fields and asserts successful score estimation.
   - **Invalid Payload Handling**: Ensures bad inputs (like incorrect categorical levels) are gracefully caught and return a client-side error (`400 Bad Request`) instead of causing server crashes (`500`).
   - **Missing Field Validation**: Confirms that missing inputs return structured client-side validation errors (`400`) instead of crashing.

---

## 🛡️ 3. Safe Git Workflow & Branch Protection

We enforce a **strict testing contract** where code is never pushed directly to the `main` branch. All developers must follow this local-first validation workflow:

### Step 1: Develop Locally
Implement your feature or bug fix on a separate branch (e.g., `feature/ui-enhancements`):
```bash
git checkout -b feature/ui-enhancements
```

### Step 2: Run Local Validation
Always run the validation tools locally:
```bash
# 1. Check for syntax bugs or undefined variables
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# 2. Run automated test suites
pytest test_model.py test_api.py -v
```
> [!WARNING]
> **If any test or lint check fails, do NOT commit or push code.** Resolve the issue and rerun the tests until you achieve a 100% success rate.

### Step 3: Create Commit & Open Pull Request
Once all checks pass, commit your changes and push them to your branch:
```bash
git add .
git commit -m "feat: implement prediction form UI enhancements and model tests"
git push origin feature/ui-enhancements
```
Open a **Pull Request (PR)** on GitHub targeting the `main` branch.

### Step 4: GitHub Actions CI Validation
Once the PR is opened, the GitHub Actions pipeline is triggered automatically. The pipeline:
1. Checks out the branch.
2. Initializes Python 3.9.
3. Installs requirements.
4. Performs code linting with `flake8`.
5. Executes `test_model.py` and `test_api.py`.

### Step 5: Merge & Deploy
Only when the GitHub Actions CI checks **pass successfully**, a repository administrator can merge the PR into `main`, which automatically triggers the Render production deployment.

### 🔒 Recommended GitHub Branch Protection Rules
Configure the following settings in your GitHub Repository under **Settings ➔ Branches**:
1. **Require a Pull Request before merging**: Prevent direct pushes to `main`.
2. **Require status checks to pass before merging**: Select the name of your GitHub Actions workflow job (e.g., `validate`). This makes it impossible to merge failing code.
3. **Require conversation resolution before merging**: Assures all developer comments are addressed.

---

## 🚀 4. GitHub Actions CI Configuration

The automated pipeline is defined in `.github/workflows/ci.yml`. It is triggered on every **Push to `main`** or **Pull Request targeting `main`**:

```yaml
name: PredictEd CI/CD Validation Pipeline
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
...
```

The pipeline runs in a isolated Ubuntu environment and will fail automatically (blocking merges and deployments) if:
- Any Python file contains syntax errors or unresolved imports.
- Any unit test fails to load the model or returns an incorrect prediction shape or value.
- Any endpoint returns status codes other than expected.

---

## ☁️ 5. Render Production Auto Deployment

Render is configured to dynamically sync with our repository and update production only when tests pass and code is successfully merged into `main`.

### Build & Deploy Settings:
* **Repository**: `https://github.com/<user>/Performance-tracker`
* **Branch**: `main`
* **Runtime**: `Python`
* **Build Command**:
  ```bash
  pip install -r requirements.txt
  ```
* **Start Command**:
  ```bash
  gunicorn app:app
  ```

### Required Environment Variables on Render:
Configure the following key-value pairs in the Render Environment Dashboard:
* `PYTHON_VERSION`: `3.9.5` (or matches your local environment)
* `DATABASE_URL`: `postgresql://<user>:<password>@<host>/<database>` (For the Postgres hybrid model backup fallback)

### Safe Auto-Deploy Workflow:
1. Under **Deploy Settings** in Render, set **Auto-Deploy** to `Yes`.
2. Because GitHub branch protection prevents merging unless GitHub Actions checks pass, **Render will only build and deploy code that has been thoroughly tested and validated.**

---

## 🔍 6. Advanced Troubleshooting Guide

### Issue A: Model Loading Fails (`"Model failed to load"`)
- **Symptoms**: Predicting from the web UI returns an API error or `test_model.py` fails during the loading step.
- **Diagnostics**:
  - Check whether `model.pkl` is located in the root repository directory next to `app.py`.
  - Verify that the pathing logic uses `os.path.abspath(__file__)` which guarantees safe resolution inside Render container directories regardless of working directory.
  - If local loading fails, the backend will attempt a fallback load from the PostgreSQL database using `DATABASE_URL`. Ensure your database is initialized and contains the active model record.

### Issue B: Categorical/Feature Encoding Mismatch
- **Symptoms**: Predicting returns HTTP `400` indicating *"Invalid or missing value for field..."*
- **Diagnostics**:
  - The model expects exact variable strings (e.g., `'Public'`, `'Private'`, `'Negative'`, `'Neutral'`, `'Positive'`).
  - If you change frontend form options, ensure that you map them in the backend `predict()` payload preprocessing before sending them to `CATEGORICAL_MAPPINGS` (e.g. mapping `Government` to `Public`).
  - Make sure all 21 model features listed in `FEATURE_COLUMNS` match the column names of the generated `pandas.DataFrame` exactly, in both casing and order.

### Issue C: Render Cold Start / API Timeout
- **Symptoms**: The first prediction request after a deploy takes a long time or returns a timeout error.
- **Diagnostics**:
  - PredictEd utilizes **Lazy Model Loading** and a **Global Model Cache**. The ML model is not loaded during Flask startup (which prevents Render startup crashes) but on the very first API request.
  - Once loaded, the model is cached in memory.
  - Use the GET `/health` endpoint to warm up the instance or verify container status before sending bulk user predictions.
