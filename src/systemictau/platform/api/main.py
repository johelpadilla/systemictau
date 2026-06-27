from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, WebSocket, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from pydantic import BaseModel
import numpy as np
import io

try:
    import pandas as pd
except ImportError:
    pass

from systemictau import systemic_tau, from_dataframe
from systemictau.layers import (
    hyper_persistence, rolling_rqa, critical_mass_metric,
    compute_antisynchronization, extract_joint_episodes,
    detect_reorganization_frob, detect_reorganization_ks, consensus_transition
)
from systemictau.recd import compute_recd_increments

app = FastAPI(title="Systemic Tau Enterprise API v4.0", version="4.0.0")

# Security
security = HTTPBearer()
SECRET_KEY = "systemictau_super_secret"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

class ComputeTauRequest(BaseModel):
    data: list[list[float]]
    window_size: int = 13
    engine: str = "numba"
    imputation: str = "linear"

class LayersRequest(BaseModel):
    taus_global: list[float]
    taus_per_module: list[list[float]]
    theta_A: float = 0.04
    theta_M: float = 1.0
    D_min: int = 30

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

def _compute_background_task(data: list[list[float]], window_size: int, task_id: str):
    # Deprecated in favor of Celery, kept for backwards compatibility
    pass

@app.post("/compute/tau/async")
def compute_tau_async(request: ComputeTauRequest, user: dict = Depends(verify_token)):
    try:
        from systemictau.platform.api.worker import compute_tau_heavy_task
        task = compute_tau_heavy_task.delay(request.data, request.window_size, request.engine)
        return {"message": "Computation started in Celery", "task_id": task.id}
    except ImportError:
        raise HTTPException(status_code=500, detail="Celery worker module not found.")

@app.websocket("/ws/stream")
async def stream_tau_updates(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # In a real scenario, process incoming stream chunks
            await websocket.send_text(f"Processed stream chunk. Current Tau: {np.random.rand()}")
    except Exception as e:
        print(f"WebSocket closed: {e}")

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

@app.post("/layers/joint_episodes")
def get_joint_episodes(request: LayersRequest):
    taus = np.array(request.taus_global, dtype=float)
    taus_pm = np.array(request.taus_per_module, dtype=float)
    
    try:
        hp_z, core_hyper = hyper_persistence(taus)
        lam, tt = rolling_rqa(taus)
        M = critical_mass_metric(hp_z, lam, tt)
        A = compute_antisynchronization(taus_pm)
        
        episodes = extract_joint_episodes(A, M, theta_A=request.theta_A, D_min=request.D_min, theta_M=request.theta_M)
        return {"episodes": episodes}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/detect/ascent")
def detect_ascent(request: LayersRequest):
    taus = np.array(request.taus_global, dtype=float)
    taus_pm = np.array(request.taus_per_module, dtype=float)
    
    try:
        t_frob, _ = detect_reorganization_frob(taus_pm)
        dtk = compute_recd_increments(taus)
        t_ks, _ = detect_reorganization_ks(dtk)
        t_star = consensus_transition(t_frob, t_ks)
        
        return {
            "t_frob": t_frob,
            "t_ks": t_ks,
            "t_star": t_star
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
