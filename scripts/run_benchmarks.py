import numpy as np
import pandas as pd
from systemictau import ChaosGenerator, compute_taus
from systemictau.layers import hyper_persistence, rolling_rqa, critical_mass_metric, extract_joint_episodes
from systemictau.validation import evaluate_early_warning
import time

def run_benchmark():
    print("Running Validation Benchmark...")
    T = 1000
    N = 10
    
    # 1. Generate Data with ChaosGenerator
    X = ChaosGenerator.logistic_map_coupled(T, N, coupling=0.1)
    
    # 2. Compute Systemic Tau
    start_time = time.time()
    taus_global, _ = compute_taus(X, window_size=13)
    tau_time = time.time() - start_time
    
    # 3. Simulate Ground Truth (e.g. outbreak after t=700)
    truth = np.zeros(T)
    truth[700:750] = 1
    
    # 4. Capas
    hp_z, core_hyper = hyper_persistence(taus_global)
    lam, tt = rolling_rqa(taus_global)
    M = critical_mass_metric(hp_z, lam, tt)
    
    # Normalize M to [0, 1] for AUC
    M_norm = (M - np.nanmin(M)) / (np.nanmax(M) - np.nanmin(M) + 1e-9)
    M_norm = np.nan_to_num(M_norm, 0.0)
    
    metrics = evaluate_early_warning(M_norm, truth, threshold=0.7)
    
    print(f"Computation Time: {tau_time:.3f}s")
    print(f"Systemic Tau Metrics: {metrics}")
    
    # Compare against traditional variance
    # Rolling variance over window
    variance_signal = np.zeros(T)
    for t in range(13, T):
        variance_signal[t] = np.var(X[t-13:t, :])
        
    v_norm = (variance_signal - np.nanmin(variance_signal)) / (np.nanmax(variance_signal) - np.nanmin(variance_signal) + 1e-9)
    v_norm = np.nan_to_num(v_norm, 0.0)
    v_metrics = evaluate_early_warning(v_norm, truth, threshold=0.7)
    
    results = [
        {"method": "Systemic Tau (M-metric)", "AUC": metrics['auc'], "Lead_Time": metrics['avg_lead_time_steps'], "FAR": metrics['false_alarm_rate'], "Precision": metrics['precision']},
        {"method": "Variance (Traditional)", "AUC": v_metrics['auc'], "Lead_Time": v_metrics['avg_lead_time_steps'], "FAR": v_metrics['false_alarm_rate'], "Precision": v_metrics['precision']}
    ]
    
    df = pd.DataFrame(results)
    df.to_csv("benchmark_results.csv", index=False)
    print("Saved benchmark_results.csv")
    return df

if __name__ == "__main__":
    df = run_benchmark()
    print(df)
