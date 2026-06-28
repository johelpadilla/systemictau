# Systemic Tau: Quick Start Guide & User Manual

Welcome to **Systemic Tau**, an advanced analytical engine designed to detect hidden structural breaks, regime shifts, and early warning signals (EWS) in complex time-series data. 

This guide will walk you through the core functionalities of the Desktop Application so you can start analyzing your data immediately.

---

## 1. Getting Started

1. **Launch the App:** Open `SystemicTau.app`.
2. **Load Data:** Click the **"Load Data (CSV/Excel)"** button in the top bar.
   * *Requirement:* Your file must contain numerical columns. The app will automatically attempt to identify a time/date column.
3. **Target Parameter:** Once loaded, go to the left sidebar and select the main numerical column you want to analyze from the **Target Parameter ($\tau_s$)** dropdown. 
4. **Analyze:** Click the large **"▶ Run Deterministic Analysis"** button to execute the mathematical engine.

---

## 2. Understanding the Sidebar Tools (Data Preparation)

Before running an analysis, you can fine-tune your data processing using the left sidebar:

* **Time Variable (X-Axis):** Allows you to explicitly choose which column represents Time. If left on `[Auto Detect]`, the engine will try to find a date column or use the raw row index.
* **Missing Data Strategy:** How to handle empty cells (`NaNs`):
  * *Prompt Me:* Asks you what to do when missing data is found.
  * *Auto-Interpolate:* Silently fills gaps using mathematical interpolation (Best for continuous signals).
  * *Strict (Abort):* Halts the analysis if your data isn't perfectly clean.
* **Signal Smoothing:** Removes stochastic (random) high-frequency noise from your data *before* looking for anomalies.
  * *Moving Average:* A simple 3-point rolling average.
  * *Savitzky-Golay:* Advanced polynomial smoothing that removes noise without destroying the underlying peaks and shapes of your data. (Highly recommended for physical sensor data).
* **Secondary Overlay:** Allows you to plot a second variable on top of your target parameter in the visualization graph for visual comparison.
* **Systemic Memory (Window):** The sliding window size used to calculate rolling variance. A larger window detects slow, macro-regime shifts. A smaller window detects rapid, sudden crashes. Click **"⚡ Auto-Optimize Window"** to let the engine mathematically find the perfect window size for your specific dataset.

---

## 3. Interpreting the Report (The Math)

When you run the analysis, the engine evaluates your data using a strict deterministic pipeline. The most important metrics are:

### The P-Value (The "Alarm" Color)
The system uses a Monte Carlo simulation (shuffling your data 500 times) to prove if a spike in variance is real or just random luck.
* **🔴 RED (Significant / p < 0.05):** A true structural break was found. The system is fundamentally changing states.
* **🟢 GREEN (Not Significant / p > 0.05):** The variance is within normal stochastic boundaries. No critical anomaly detected.

### Key Metrics
* **Signal-to-Noise Ratio (SNR):** How "loud" the anomaly is compared to the normal background noise of the system. An SNR > 3.0 indicates a massive structural shock.
* **Entropic Decay:** Measures how fast the system's predictability is collapsing. High entropy usually precedes a crash.
* **Max Acceleration:** The second derivative of your data. It shows the raw kinetic force pushing the system into the new regime.

---

## 4. Advanced Features

* **Animate Phase Space:** Once an analysis is complete, click this button to visualize the system's trajectory in a 2D phase-space plot. It dynamically shows how the system orbits an attractor before breaking away during a regime shift.
* **Save Analysis & Compare:** Use the top bar to save your report as a `.tau` file. Later, you can load a new dataset and use **"Compare with File"** to mathematically benchmark the current anomaly against a past historical crisis.
* **Enable AI Agents (Epistemic Engine):** Toggle this switch to activate the autonomous AI. It will read your mathematical report and attempt to provide a human-readable hypothesis explaining *why* the system broke down. *(Requires configuring a Google Gemini API Key in Advanced Settings).*
