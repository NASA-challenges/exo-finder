# Exo-Finder

Exo-Finder is a small research demo that provides tools to explore NASA exoplanet candidate datasets (Kepler, TESS, K2) and run a machine learning model to predict exoplanet candidate dispositions. It includes:

- A Flask backend (`nasa-backend`) that serves API endpoints and performs predictions using a pre-trained model.
- A React frontend (`nasa-frontend`) that hosts a simple UI for single and batch predictions and exploration of the CSV datasets.
- Model artifacts and helper scripts (in the repo) used to load or upload models.

This README covers how to set up, run and troubleshoot the project on a development machine (Windows PowerShell examples included).

## Table of contents

- What’s in this repo
- Requirements
- Backend: setup & run
- Frontend: setup & run
- API reference (important endpoints)
- Data and model notes
- Troubleshooting
- Contributing
- License

## What’s in this repo

- `nasa-backend/` — Flask application that exposes web APIs for:
	- model predictions (`/predict`, `/batch_predict`)
	- CSV-backed NASA data (`/api/exoplanets/kepler`, `/api/exoplanets/tess`, `/api/exoplanets/k2`, `/api/exoplanets/summary`)
	- health check (`/api/health`)
- `nasa-frontend/` — React frontend (Create React App) used to upload files, run single predictions, and explore datasets.
- `Nasa/` — helper scripts, pre-trained model artifacts, pickled encoders/scalers and CSV data used by the backend.
- `README.md`, `LICENSE` — project documentation and licensing.

## Requirements

- Python 3.10+ (recommended)
- Node.js 16+ and npm (for the frontend)
- Internet access for the backend to download model files from Hugging Face (the Flask app uses `huggingface_hub` to fetch artifacts at runtime).

Recommended Python packages (if a `requirements.txt` is not present):

```powershell
pip install flask flask-cors pandas numpy scikit-learn xgboost huggingface-hub
```

Note: if you already have a `requirements.txt` in the project, use that:

```powershell
pip install -r requirements.txt
```

## Backend — setup & run (Windows PowerShell)

1. Create and activate a virtual environment (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install Python dependencies (see Requirements above).

3. Ensure the CSV data files are present in `nasa-backend/data/`. The backend expects the following CSV files:

- `kepler_koi.csv`
- `tess_toi.csv`
- `k2_candidates.csv`

If they are missing, either add them to the `nasa-backend/data/` directory or update the code to point to your data path.

4. Start the Flask backend (the app script runs the server when executed directly):

```powershell
python .\nasa-backend\app.py
```

By default the backend will run on port 5000 (http://localhost:5000). The first run may download model files using the Hugging Face hub API; ensure your environment has network access and set the HF token as needed if artifacts are private.

## Frontend — setup & run

1. Change into the frontend folder and install dependencies:

```powershell
cd nasa-frontend
npm install
```

2. Run the frontend in development mode:

```powershell
npm start
```

The React dev server typically opens at http://localhost:3000 and communicates with the backend at the API endpoints described below.

If the frontend needs a different backend host/port, update its configuration or the proxy setting in `nasa-frontend/package.json`.

## API reference (key endpoints)

- GET / — Basic health/info endpoint with available endpoints.
- POST /predict — Accepts JSON payload for a single sample and returns a prediction and probabilities. Example payload is a mapping of feature names to values.
- POST /batch_predict — Accepts a multipart/form-data upload with a CSV file under field name `file`. Returns a CSV with predicted labels and probability columns.
- GET /api/exoplanets/kepler — Returns transformed Kepler KOI records as JSON suitable for frontend consumption.
- GET /api/exoplanets/tess — Returns transformed TESS TOI records as JSON.
- GET /api/exoplanets/k2 — Returns transformed K2 candidate records as JSON.
- GET /api/exoplanets/summary — Returns summary statistics across the available CSV datasets.
- GET /api/health — Returns a basic health JSON with timestamp and whether expected data files exist.

Example: single prediction with curl (PowerShell):

```powershell
# Example JSON body; replace with actual feature names/values expected by the model
$body = '{"feature_A": 1.23, "feature_B": 4.56}'
Invoke-RestMethod -Uri http://localhost:5000/predict -Method Post -Body $body -ContentType 'application/json'
```

Example: batch prediction upload (PowerShell):

```powershell
Invoke-RestMethod -Uri http://localhost:5000/batch_predict -Method Post -InFile .\sample_batch.csv -ContentType 'multipart/form-data'
```

Note: the React frontend provides UI wrappers for single and batch predictions.

## Data and model notes

- The backend code will download ML artifacts with `huggingface_hub.hf_hub_download` when started. If the models are private you will need to configure a Hugging Face token in your environment (`HF_HOME`, `HUGGINGFACE_HUB_TOKEN`, or local login) before running the backend.
- The repo contains pickled files and helper scripts in the `Nasa/` directory; these are used during development and training. The production app expects the model files available locally or downloaded from HF.

## Troubleshooting

- If the backend raises errors about missing CSV files, ensure the files are placed in `nasa-backend/data/` and named exactly as listed above.
- If Python import errors occur, confirm your virtual environment is activated and dependencies installed.
- If model downloads fail, ensure you have network access and a valid HF token if artifacts are private.
- If you encounter syntax errors in `nasa-backend/app.py` after edits, make sure indentation is consistent (Python is indentation-sensitive). The main entrypoint is `python nasa-backend/app.py`.

Useful dev checks:

```powershell
# Check Python version
python --version

# Verify backend starts and prints the data-file status lines
python .\nasa-backend\app.py

# Run unit or smoke tests if present (example):
python test.py
```

## Contributing

Contributions are welcome. Please follow standard git workflows:

1. Create a topic branch for your change:

```powershell
git checkout -b feature/my-change
```

2. Make edits, run tests and commit.
3. Open a PR against `main` when ready for review.

## License

This repository includes a `LICENSE` file; please review it for licensing details.

