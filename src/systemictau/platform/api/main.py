from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import numpy as np
import io

try:
    import pandas as pd
except ImportError:
    pass

from systemictau import systemic_tau, from_dataframe

app = FastAPI(
    title="Systemic Tau API",
    description="REST API for computing Systemic Tau and Ontological Ascent layers.",
    version="3.0.0-dev"
)

class ComputeTauRequest(BaseModel):
    data: list[list[float]]
    window_size: int = 13
    imputation: str = "linear"

@app.get("/")
def read_root():
    return {"message": "Welcome to the Systemic Tau API. Visit /docs for the swagger UI."}

@app.post("/compute/tau")
def compute_tau(request: ComputeTauRequest):
    """
    Computes Systemic Tau from a raw JSON payload (matrix of size T x N).
    """
    try:
        X = np.array(request.data)
        if X.ndim != 2:
            raise ValueError("Data must be a 2D matrix.")
            
        res = systemic_tau(X, window_size=request.window_size)
        
        # Replace NaNs with None for JSON serialization
        global_taus = [x if not np.isnan(x) else None for x in res.taus_global]
        
        return {
            "taus_global": global_taus,
            "metadata": res.metadata
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/compute/tau/csv")
async def compute_tau_csv(file: UploadFile = File(...), window_size: int = 13):
    """
    Upload a CSV file to compute Systemic Tau.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        res = from_dataframe(df, window_size=window_size)
        
        global_taus = [x if not np.isnan(x) else None for x in res.taus_global]
        
        return {
            "taus_global": global_taus,
            "metadata": res.metadata
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
