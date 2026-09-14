"""FastAPI entry point for the synthetic medicine shortage prototype."""

import math
import sys
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# Existing modules are also runnable as scripts, so make their imports work
# when this file is loaded as ``backend.main`` by Uvicorn.
BACKEND_DIRECTORY = Path(__file__).resolve().parent
if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIRECTORY))

from redistribution import generate_recommendations  # noqa: E402
from ripple import simulate_ripple  # noqa: E402
from shortage import analyze_shortage, get_critical_shortages  # noqa: E402


app = FastAPI(
    title="Medicine Shortage Prediction API",
    description="Synthetic hackathon prototype for demand, shortage, and redistribution analysis.",
    version="1.0.0",
)


class RippleSimulationRequest(BaseModel):
    hospital_id: str
    medicine_id: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5177",
        "http://127.0.0.1:5177",
        "http://localhost:5178",
        "http://127.0.0.1:5178",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _json_value(value):
    """Convert pandas and NumPy values into standard JSON-compatible values."""
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _dataframe_records(dataframe):
    """Return DataFrame rows in a form FastAPI can serialize reliably."""
    return _json_value(dataframe.to_dict(orient="records"))


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    """Return a small JSON error instead of an HTML server error page."""
    return JSONResponse(
        status_code=500,
        content={"error": "Unable to complete the requested analysis.", "detail": str(exc)},
    )


@app.get("/")
def root():
    """Confirm that the API process is running."""
    return {"message": "Medicine Shortage Prediction API", "status": "running"}


@app.get("/health")
def health():
    """Return a simple health response for local monitoring."""
    return {"status": "healthy"}


@app.get("/shortages")
def shortages():
    """Run and return the existing shortage analysis."""
    return _dataframe_records(analyze_shortage())


@app.get("/shortages/critical")
def critical_shortages():
    """Return only shortage rows with CRITICAL status."""
    return _dataframe_records(get_critical_shortages())


@app.get("/redistribution")
def redistribution():
    """Run and return the existing redistribution recommendations."""
    return _dataframe_records(generate_recommendations())


@app.get("/summary")
def summary():
    """Return counts suitable for a future dashboard."""
    shortage_data = analyze_shortage()
    recommendations = generate_recommendations()
    status_counts = shortage_data["status"].value_counts()
    return {
        "total_hospitals": int(shortage_data["hospital_id"].nunique()),
        "total_medicines": int(shortage_data["medicine_id"].nunique()),
        "critical_shortages": int(status_counts.get("CRITICAL", 0)),
        "warning_shortages": int(status_counts.get("WARNING", 0)),
        "monitor_cases": int(status_counts.get("MONITOR", 0)),
        "safe_cases": int(status_counts.get("SAFE", 0)),
        "total_redistribution_recommendations": int(len(recommendations)),
    }


@app.post("/ripple/simulate")
def ripple_simulate(request: RippleSimulationRequest):
    """Simulate a recommended transfer without changing inventory data."""
    try:
        return _json_value(simulate_ripple(request.hospital_id, request.medicine_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc