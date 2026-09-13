# Medicine Shortage Prediction and Redistribution System

## Problem
Hospitals can unexpectedly run out of important medicines while nearby hospitals have surplus stock. This can delay treatment and make emergency purchasing more expensive.

## Proposed solution
This project will use hospital inventory and historical demand data to:

1. Predict which medicines may become shortages soon.
2. Identify nearby hospitals with surplus stock.
3. Recommend possible medicine redistribution between hospitals.

The data in this prototype is fully synthetic and contains no patient information.

## Current project stage
**Stage 6: React dashboard**

The project contains synthetic demand prediction, shortage detection, redistribution recommendations, a local FastAPI backend, and a React dashboard. The dashboard is intended for this hackathon prototype and uses only the synthetic project data.

## Technology planned
- Python for data processing and machine learning
- pandas for working with CSV data
- scikit-learn for a basic demand prediction model
- FastAPI and Uvicorn for the local backend API
- React and Vite for the dashboard frontend
- HTML/CSS/JavaScript through the React toolchain

Python and frontend dependencies are installed separately using the setup commands below.

## Folder guide

- `backend/`: API and analysis logic
- `data/`: synthetic input datasets used by the project
- `models/`: future trained model files
- `notebooks/`: future beginner-friendly data exploration and model experiments
- `frontend/`: Vite React dashboard
- `README.md`: project overview and setup notes
- `requirements.txt`: Python libraries planned for later stages
- `.gitignore`: files and folders that should not be committed to Git

## Synthetic data files

- `data/hospitals.csv`: fictional hospitals and fictional map coordinates
- `data/hospital_inventory.csv`: current medicine stock, usage, lead time, and price
- `data/historical_demand.csv`: dated synthetic daily medicine demand observations

## Start the API

Install the Python dependencies, then run the backend from the project root:

```powershell
python -m pip install -r requirements.txt
uvicorn backend.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive documentation is available at `http://127.0.0.1:8000/docs`.

To run the endpoint checks:

```powershell
python backend/test_api.py
```

## Start the frontend

In a second terminal, install the frontend dependencies and start Vite:

```powershell
cd frontend
npm install
npm run dev
```

The frontend reads from `http://127.0.0.1:8000`. Run both the backend and frontend during the demo:

```powershell
# Terminal 1, from the project root
uvicorn backend.main:app --reload

# Terminal 2, from the frontend folder
npm run dev
```

This is a synthetic hackathon prototype. It has no authentication, payment system, or real patient information.
