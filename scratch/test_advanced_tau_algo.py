import pandas as pd
import numpy as np
import scipy.stats as stats

# Load data
df = pd.read_excel("Aedes2yrs_with_coordinates.xlsx")

# Let's take a single NID for simplicity, say NID=13 which was the leading driver
df_13 = df[df['NID'] == 13].copy()
df_13 = df_13.sort_values(by='EpiWeek')

data = df_13['Count'].values
window = 20
T = len(data)

# Baseline AR-1
ar1 = []
for i in range(window, T+1):
    win = data[i-window:i]
    if len(win) < 2:
        ar1.append(0)
    else:
        # Pearson correlation
        corr = np.corrcoef(win[:-1], win[1:])[0, 1]
        ar1.append(corr if not np.isnan(corr) else 0)

# Non-linear "Mutual Information" approximation using histogram-based Shannon Entropy
def calc_mi(x, y, bins=5):
    c_xy = np.histogram2d(x, y, bins)[0]
    mi = stats.entropy(c_xy.flatten())
    return mi

mi_rolling = []
for i in range(window, T+1):
    win = data[i-window:i]
    if len(win) < 2:
        mi_rolling.append(0)
    else:
        mi = calc_mi(win[:-1], win[1:])
        mi_rolling.append(mi)

# Dynamic Windowing prototype
dynamic_var = []
current_window = 20
for i in range(20, T+1):
    # Base variance over current window
    win = data[i-current_window:i]
    v = np.var(win)
    dynamic_var.append(v)
    
    # Adapt window: if highly volatile, shrink window to be more sensitive
    # if stable, expand window to capture macro trend
    if v > np.mean(dynamic_var) * 1.5:
        current_window = max(10, current_window - 2)
    else:
        current_window = min(40, current_window + 1)
        
print("Baseline AR1:", ar1[-5:])
print("Non-linear MI:", mi_rolling[-5:])
print("Dynamic Var:", dynamic_var[-5:])
print("Experiment script ran successfully.")
