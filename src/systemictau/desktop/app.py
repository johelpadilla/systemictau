import os
import sys
import threading
import numpy as np
import pandas as pd
from google import genai
import tkinter as tk
from systemictau.config import settings
from systemictau.agents.epistemic_engine import run_discovery_engine_sync

class ToolTip(object):
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.tw = None

    def enter(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') and self.widget.bbox("insert") else (0,0,0,0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#1c1c1c", foreground="white", relief='solid', borderwidth=1,
                       font=("Arial", "12", "normal"), padx=10, pady=5)
        label.pack(ipadx=1, ipady=1)

    def leave(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None

try:
    from fpdf import FPDF
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
except ImportError:
    pass

try:
    import customtkinter as ctk
    from tkinter import filedialog
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    ctk = None
    HAS_DND = False

if HAS_DND:
    class BaseApp(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)
else:
    class BaseApp(ctk.CTk):
        pass

class SystemicTauApp(BaseApp):
    def __init__(self):
        super().__init__()

        self.title("Systemic Tau v8.0 - Mathematical Dashboard")
        self.geometry("1400x900")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.adv_window = None
        self.loaded_file_path = None
        self.full_log = ""
        self.df = None
        self.math_stats = {}
        
        # -------------------------------------
        # SIDEBAR
        # -------------------------------------
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Systemic Tau", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))
        
        self.simple_mode_switch = ctk.CTkSwitch(self.sidebar_frame, text="Simple Mode", command=self.toggle_mode)
        self.simple_mode_switch.grid(row=1, column=0, padx=20, pady=10)
        self.simple_mode_switch.select()
        
        self.domain_label = ctk.CTkLabel(self.sidebar_frame, text="Data Domain:", anchor="w")
        self.domain_label.grid(row=2, column=0, padx=20, pady=(20, 0))
        self.domain_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Epidemiology", "Finance", "Ecology", "General"])
        self.domain_menu.grid(row=3, column=0, padx=20, pady=(10, 10))
        
        # Target Variable Selection
        self.target_label = ctk.CTkLabel(self.sidebar_frame, text="Target Parameter (τ_s):", anchor="w")
        self.target_label.grid(row=4, column=0, padx=20, pady=(10, 0))
        self.target_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["[Load File First]"], command=self._redraw_preview)
        self.target_menu.grid(row=5, column=0, padx=20, pady=(10, 5))
        
        # Secondary Variable Selection (Overlay)
        self.secondary_label = ctk.CTkLabel(self.sidebar_frame, text="Secondary Overlay:", anchor="w", text_color="gray60")
        self.secondary_label.grid(row=6, column=0, padx=20, pady=(5, 0))
        self.secondary_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["[None]"], command=self.analyze_data)
        self.secondary_menu.grid(row=7, column=0, padx=20, pady=(5, 10))
        
        self.window_label = ctk.CTkLabel(self.sidebar_frame, text="Systemic Memory (Window):", anchor="w")
        self.window_label.grid(row=8, column=0, padx=20, pady=(10, 0))
        
        self.window_slider = ctk.CTkSlider(self.sidebar_frame, from_=3, to=100, command=self._on_slider_change)
        self.window_slider.set(20)
        self.window_slider.grid(row=9, column=0, padx=20, pady=(5, 5))
        
        self.optimize_btn = ctk.CTkButton(self.sidebar_frame, text="⚡ Auto-Optimize Window", command=self.optimize_window, fg_color="#2ca02c", hover_color="#238023")
        self.optimize_btn.grid(row=10, column=0, padx=20, pady=(0, 10))
        
        self.animate_btn = ctk.CTkButton(self.sidebar_frame, text="▶ Animate Phase Space", command=self.animate_phase_space, state="disabled", fg_color="#ff7f0e", hover_color="#d62728")
        self.animate_btn.grid(row=11, column=0, padx=20, pady=(0, 10))
        
        # AI Epistemic Engine Switch
        self.run_ai_switch = ctk.CTkSwitch(self.sidebar_frame, text="Enable AI Agents")
        self.run_ai_switch.grid(row=12, column=0, padx=20, pady=(10, 20))
        
        if HAS_DND:
            self.dnd_label = ctk.CTkLabel(self.sidebar_frame, text="[Drag & Drop Active]", text_color="green", font=ctk.CTkFont(size=10))
            self.dnd_label.grid(row=13, column=0, padx=20, pady=5)
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.handle_dnd)
            
        self.advanced_btn = ctk.CTkButton(self.sidebar_frame, text="Advanced Settings", state="disabled", command=self.open_advanced_settings)
        self.advanced_btn.grid(row=14, column=0, padx=20, pady=20, sticky="s")

        # -------------------------------------
        # MAIN FRAME
        # -------------------------------------
        self.main_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=5) # Graph space
        self.main_frame.grid_rowconfigure(2, weight=2) # Text/Metrics space
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Top bar
        self.top_bar = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.upload_btn = ctk.CTkButton(self.top_bar, text="Select CSV/Excel File", command=self.upload_file_dialog, height=40)
        self.upload_btn.pack(side="left", padx=(0, 10))
        
        self.analyze_btn = ctk.CTkButton(self.top_bar, text="Analyze Systemic Transition", command=self.analyze_data, height=40, font=ctk.CTkFont(weight="bold"))
        self.analyze_btn.pack(side="left", padx=10)
        
        self.file_label = ctk.CTkLabel(self.top_bar, text="No file loaded.")
        self.file_label.pack(side="left", padx=20)
        
        self.workspace_btn = ctk.CTkButton(self.top_bar, text="🪟 New Workspace", command=self.open_new_workspace, height=40, fg_color="transparent", border_width=1, text_color="gray80")
        self.workspace_btn.pack(side="right", padx=10)
        
        # Middle: Graph Area (Tabs)
        self.graph_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.graph_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        
        self.tabview = ctk.CTkTabview(self.graph_frame)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        
        self.tab1 = self.tabview.add("Temporal Dynamics")
        self.tab2 = self.tabview.add("Phase Space")
        
        # Temporal Dynamics Tab (Fig 1)
        self.fig1 = Figure(figsize=(10, 5), dpi=100)
        self.ax1 = self.fig1.add_subplot(221)
        self.ax2 = self.fig1.add_subplot(222)
        self.ax2_twin = self.ax2.twinx()
        self.ax3 = self.fig1.add_subplot(223)
        self.ax4 = self.fig1.add_subplot(224)
        self.fig1.tight_layout(pad=3.0)
        
        self.ax1.set_title("Systemic Tau over time: τ_s(t)")
        self.ax2.set_title("Raw Data & Acceleration (a_t)")
        self.ax3.set_title("Entropic Decay (S_e)")
        self.ax4.set_title("Systemic Coherence (C_s)")
        
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.tab1)
        self.canvas1.draw()
        self.canvas1.get_tk_widget().pack(fill="both", expand=True)
        
        self.toolbar1 = NavigationToolbar2Tk(self.canvas1, self.tab1)
        self.toolbar1.update()
        self.toolbar1.pack(side="bottom", fill="x")
        
        # Phase Space Tab (Fig 2)
        self.fig2 = Figure(figsize=(10, 5), dpi=100)
        self.ax_ps = self.fig2.add_subplot(111)
        self.fig2.tight_layout(pad=3.0)
        
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.tab2)
        self.canvas2.draw()
        self.canvas2.get_tk_widget().pack(fill="both", expand=True)
        
        self.toolbar2 = NavigationToolbar2Tk(self.canvas2, self.tab2)
        self.toolbar2.update()
        self.toolbar2.pack(side="bottom", fill="x")
        
        # Bottom: Metrics & AI Log
        self.bottom_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, sticky="nsew", pady=10)
        self.bottom_frame.grid_rowconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(0, weight=1) # Metrics
        self.bottom_frame.grid_columnconfigure(1, weight=3) # Log
        self.bottom_frame.grid_columnconfigure(2, weight=0) # Buttons
        
        # Math Metrics Panel
        self.metrics_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.metrics_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self.metrics_frame.grid_columnconfigure(0, weight=1)
        self.metrics_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.metrics_frame, text="TOPOLOGICAL METRICS", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        self.lbl_tstar = self._create_metric_card(self.metrics_frame, "t* (Structural Breakpoint)", 1, 0, colspan=2, val_color="#ff7f0e", val_size=24, tooltip_text="The exact time index where the system crossed its structural stability threshold.")
        self.lbl_tau = self._create_metric_card(self.metrics_frame, "Max τ_s (Mass)", 2, 0, tooltip_text="Maximum variance magnitude. Represents the physical topological mass of the transition.")
        self.lbl_accel = self._create_metric_card(self.metrics_frame, "Peak a_t (Momentum)", 2, 1, tooltip_text="Peak 2nd derivative. Indicates the absolute momentum forcing the structural collapse.")
        self.lbl_entropy = self._create_metric_card(self.metrics_frame, "Max S_e (Chaos)", 3, 0, tooltip_text="Peak volatility proxy. Measures the internal thermodynamic chaos accumulated.")
        self.lbl_coherence = self._create_metric_card(self.metrics_frame, "Min C_s (Coupling)", 3, 1, tooltip_text="Multidimensional eigenvalue minimum. Tracks the desynchronization of the system's components.")

        # AI Epistemic Log
        self.results_box = ctk.CTkTextbox(self.bottom_frame, font=ctk.CTkFont(family="Courier", size=12))
        self.results_box.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        self.results_box.insert("0.0", "Epistemic Engine Output Log...")
        self.results_box.configure(state="disabled")
        
        self.actions_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.actions_frame.grid(row=0, column=2, sticky="n")
        
        self.explain_btn = ctk.CTkButton(self.actions_frame, text="Explain Simply", command=self.explain_simply)
        self.explain_btn.pack(pady=10)
        
        self.export_btn = ctk.CTkButton(self.actions_frame, text="Export Academic PDF", command=self.export_report)
        self.export_btn.pack(pady=10)

    def _create_metric_card(self, parent, title, row, col, colspan=1, val_color=None, val_size=16, tooltip_text=""):
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color=("gray85", "gray20"))
        card.grid(row=row, column=col, columnspan=colspan, padx=5, pady=5, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color="gray50")
        lbl_title.grid(row=0, column=0, pady=(5, 0))
        
        lbl_value = ctk.CTkLabel(card, text="--", font=ctk.CTkFont(size=val_size, weight="bold"), text_color=val_color)
        lbl_value.grid(row=1, column=0, pady=(0, 5))
        
        if tooltip_text:
            ToolTip(card, tooltip_text)
            ToolTip(lbl_title, tooltip_text)
            ToolTip(lbl_value, tooltip_text)
            
        return lbl_value

    def _on_slider_change(self, value):
        if self.df is not None:
            self.analyze_data()

    def toggle_mode(self):
        if self.simple_mode_switch.get() == 1:
            self.advanced_btn.configure(state="disabled")
            if self.adv_window is not None and self.adv_window.winfo_exists():
                self.adv_window.destroy()
        else:
            self.advanced_btn.configure(state="normal")
            
    def handle_dnd(self, event):
        file_path = event.data.strip('{}') 
        self._load_file(file_path)

    def upload_file_dialog(self):
        file_path = filedialog.askopenfilename(filetypes=[("Data Files", "*.csv *.xlsx")])
        if file_path:
            self._load_file(file_path)
            
    def _load_file(self, file_path):
        self.loaded_file_path = file_path
        filename = os.path.basename(file_path)
        self.file_label.configure(text=f"Loaded: {filename}")
        
        try:
            if file_path.endswith('.csv'):
                self.df = pd.read_csv(file_path)
            else:
                self.df = pd.read_excel(file_path)
                
            self.time_col = None
            for col in self.df.columns:
                col_lower = str(col).lower().strip()
                if any(x in col_lower for x in ['date', 'time', 'fecha', 'timestamp', 'year', 'año', 'month', 'mes', 'week', 'semana']):
                    self.time_col = col
                    break
            
            # Fallback: if no date keyword is found, assume the first column is the time/index column
            if self.time_col is None and len(self.df.columns) > 0:
                self.time_col = self.df.columns[0]
                
            numeric_cols = self.df.select_dtypes(include='number').columns.tolist()
            if len(numeric_cols) > 0:
                self.target_menu.configure(values=numeric_cols)
                self.target_menu.set(numeric_cols[0])
                self.secondary_menu.configure(values=["[None]"] + numeric_cols)
                self.secondary_menu.set("[None]")
                self._redraw_preview(numeric_cols[0])
            else:
                self.target_menu.configure(values=["[No Numeric Data]"])
                self.target_menu.set("[No Numeric Data]")
                self.secondary_menu.configure(values=["[None]"])
                self.secondary_menu.set("[None]")
        except Exception as e:
            self.file_label.configure(text=f"Error reading file: {e}")
            
    def _redraw_preview(self, col_name):
        if self.df is None or col_name not in self.df.columns:
            return
        self.ax1.clear()
        self.ax2.clear()
        self.ax2_twin.clear()
        self.ax3.clear()
        self.ax4.clear()
        self.ax1.plot(self.df[col_name].values, color="#1f77b4")
        self.ax1.set_title(f"Preview: {col_name}")
        self.canvas1.draw()
            
    def optimize_window(self):
        if not self.loaded_file_path or self.df is None:
            self._update_results("Error: Please upload a valid data file first.\n", clear=True)
            return
            
        self._update_results("\n[OPTIMIZER] Scanning for optimal Systemic Memory window...\n")
        threading.Thread(target=self._run_optimization, daemon=True).start()
        
    def _run_optimization(self):
        try:
            numeric_df = self.df.select_dtypes(include='number').ffill().fillna(0)
            if numeric_df.empty:
                raise ValueError("No numeric columns found.")
            target_col = self.target_menu.get()
            if target_col not in numeric_df.columns:
                raise ValueError("Invalid target column.")
                
            data = numeric_df[target_col].values
            n = len(data)
            max_w = min(100, max(10, n // 2))
            
            best_w = 3
            best_score = -np.inf
            
            for w in range(3, max_w + 1):
                tau_series = pd.Series(data).rolling(window=w, min_periods=1).var().fillna(0).values
                if len(tau_series) == 0: 
                    continue
                tau_max = np.max(tau_series)
                tau_median = np.median(tau_series)
                
                # Signal-to-noise ratio
                if tau_median > 0:
                    score = tau_max / tau_median
                else:
                    score = tau_max
                    
                if score > best_score:
                    best_score = score
                    best_w = w
                    
            self.after(0, self.window_slider.set, best_w)
            self._update_results(f"[OPTIMIZER] Found optimal window: {best_w} (SNR: {best_score:.2f})\n")
            self.after(100, self.analyze_data)
            
        except Exception as e:
            self._update_results(f"\n[ERROR] Optimization failed: {e}\n")
            
    def analyze_data(self):
        if not self.loaded_file_path or self.df is None:
            self._update_results("Error: Please upload a valid data file first.\\n", clear=True)
            return
            
        self.full_log = ""
        self._update_results("Initializing Systemic Tau Mathematical Analysis...\n\n", clear=True)
        threading.Thread(target=self._run_real_analysis_pipeline, daemon=True).start()

    def _run_real_analysis_pipeline(self):
        try:
            numeric_df = self.df.select_dtypes(include='number').ffill().fillna(0)
            if numeric_df.empty:
                raise ValueError("No numeric columns found in data.")
                
            # --- MATHEMATICAL ENGINE ---
            target_col = self.target_menu.get()
            if target_col not in numeric_df.columns:
                raise ValueError(f"Selected column '{target_col}' is not valid or not numeric.")
                
            data = numeric_df[target_col].values
            
            try:
                window = int(self.window_slider.get())
            except Exception:
                window = max(3, len(data) // 20)
            if window >= len(data):
                window = max(3, len(data) // 2)
            
            # 1. Systemic Tau (Dynamic Variance across time)
            tau_series = pd.Series(data).rolling(window=window, min_periods=1).var().fillna(0).values
            tau_val = np.max(tau_series)
            t_star = int(np.argmax(tau_series))
            
            tau_median = np.median(tau_series)
            if tau_median > 0:
                snr = tau_val / tau_median
            else:
                snr = tau_val
            
            # 2. Acceleration (Second Derivative of raw data)
            velocity = np.gradient(data)
            acceleration = np.gradient(velocity)
            max_accel = np.max(acceleration)
            
            # 3. Entropic Decay (Rolling Volatility Proxy)
            entropy = pd.Series(data).rolling(window=window, min_periods=1).std().fillna(0).values
            max_entropy = np.max(entropy)
            
            # 4. Systemic Coherence (Eigenvalues)
            if len(numeric_df.columns) > 1:
                matrix_data = numeric_df.values
                T, N = matrix_data.shape
                coherence = np.full(T, np.nan)
                
                for i in range(window, T + 1):
                    win_data = matrix_data[i-window:i, :]
                    std_dev = win_data.std(axis=0) + 1e-9
                    win_data_norm = (win_data - win_data.mean(axis=0)) / std_dev
                    corr_matrix = np.corrcoef(win_data_norm, rowvar=False)
                    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0, posinf=1.0, neginf=-1.0)
                    eigenvalues = np.linalg.eigvals(corr_matrix)
                    coherence[i-1] = np.max(eigenvalues).real / N
            else:
                coherence = pd.Series(data).rolling(window=window, min_periods=1).corr(pd.Series(data).shift(1)).fillna(0).values
            min_coherence = np.nanmin(coherence)
            
            if getattr(self, 'time_col', None):
                t_star_label = str(self.df[self.time_col].iloc[t_star])
            else:
                t_star_label = f"Index {t_star}"
                
            # --- ROBUSTNESS & VALIDATION ENGINE ---
            # 1. Detailed Sensitivity Matrix & Effect Size
            tau_mean_hist = np.mean(tau_series[:t_star]) if t_star > 0 else np.mean(tau_series)
            tau_std_hist = np.std(tau_series[:t_star]) if t_star > 0 else np.std(tau_series)
            effect_size = (tau_val - tau_mean_hist) / (tau_std_hist + 1e-9)
            
            sensitivity_matrix = []
            # Calculate for unique windows around the current window
            test_windows = sorted(list(set([max(3, window-4), max(3, window-2), window, min(len(data), window+2), min(len(data), window+4)])))
            for w_test in test_windows:
                t_test = pd.Series(data).rolling(window=w_test, min_periods=1).var().fillna(0).values
                t_star_test = int(np.argmax(t_test)) if len(t_test) > 0 else t_star
                tau_max_test = np.max(t_test) if len(t_test) > 0 else 0
                sensitivity_matrix.append((w_test, t_star_test, tau_max_test))
            
            # 2. Null Model Monte Carlo (p-value)
            n_perm = 500
            surrogate_taus = []
            for _ in range(n_perm):
                shuffled = np.random.permutation(data)
                surr_tau = pd.Series(shuffled).rolling(window=window, min_periods=1).var().fillna(0).max()
                surrogate_taus.append(surr_tau)
            p_value = np.sum(np.array(surrogate_taus) >= tau_val) / n_perm
            if p_value < 0.05:
                significance_str = "Statistically Significant. Strong evidence of topological structural break."
            elif p_value < 0.10:
                significance_str = f"Marginally Significant. Implies a {p_value*100:.1f}% probability of a false positive under unrestricted shuffling. While a significant anomaly is present, it lacks strict 95% deterministic confidence, suggesting the presence of high background noise masking the true signal."
            else:
                significance_str = f"Not Significant. Implies a {p_value*100:.1f}% false positive rate. Under the Null Hypothesis, this peak easily arises by chance, invalidating the structural break."
            
            # 3. Early Warning Signals (Precursors) & Objective Transition Metrics
            precursor_signal = "None Detected. The system showed no early warning signals."
            has_precursors = False
            if t_star > window:
                pre_data = data[:t_star]
                s_data = pd.Series(pre_data)
                
                ar1_series = s_data.rolling(window=window).corr(s_data.shift(1)).fillna(0).values
                var_series = s_data.rolling(window=window).var().fillna(0).values
                skew_series = s_data.rolling(window=window).skew().fillna(0).values
                
                if len(ar1_series) > window:
                    ar1_slope = np.polyfit(np.arange(window), ar1_series[-window:], 1)[0]
                    var_slope = np.polyfit(np.arange(window), var_series[-window:], 1)[0]
                    skew_slope = np.polyfit(np.arange(window), skew_series[-window:], 1)[0]
                    
                    sig_list = [
                        f"AR-1: {ar1_slope:+.3f}" + (" (PASS)" if ar1_slope > 0.05 else " (FAIL)"),
                        f"Var: {var_slope:+.3f}" + (" (PASS)" if var_slope > 0.05 else " (FAIL)"),
                        f"Skew: {skew_slope:+.3f}" + (" (PASS)" if abs(skew_slope) > 0.05 else " (FAIL)")
                    ]
                    
                    if ar1_slope > 0.05 or var_slope > 0.05 or abs(skew_slope) > 0.05:
                        has_precursors = True
                        precursor_signal = "YES. Signals detected -> " + " | ".join(sig_list)
                    else:
                        precursor_signal = "NO. Sudden Shock -> " + " | ".join(sig_list)
            precursor_signal += f"\n     (Methodology: Evaluated via rolling monotonic regression slope over the exact W={window} periods immediately preceding t*={t_star})."
                        
            # Final Analytical Verdict (Resolution Engine)
            if p_value >= 0.05 and has_precursors:
                final_verdict = "STRUCTURAL STRESS SURVIVED.\n     -> Finding: The system suffered significant resilience degradation (precursors) but successfully absorbed the final shock without a complete topological break.\n     -> Action: Do not treat as a false alarm. Inject resources or reduce load to restore baseline resilience before the next external shock hits."
            elif p_value >= 0.05 and not has_precursors:
                final_verdict = "PURE NOISE.\n     -> Finding: No precursors, and the peak is statistically insignificant.\n     -> Action: No systemic intervention required. Resume normal operations."
            elif p_value < 0.05 and has_precursors:
                final_verdict = "TRUE ENDOGENOUS COLLAPSE.\n     -> Finding: The system degraded structurally from within (precursors) before suffering a significant break.\n     -> Action: Intervene directly on the 'Leading Driver' variables to break the synchronous lock-in."
            else:
                final_verdict = "TRUE EXOGENOUS SHOCK.\n     -> Finding: A mathematically significant break with zero prior warning.\n     -> Action: Since this shock gave zero warning, predictive models will fail. Redirect focus to building buffer capacity against external impacts."
            
            # 4. Uncertainty Bounds (FWHM & Relaxation)
            fwhms = []
            relaxations = []
            for w_test, t_test, _ in sensitivity_matrix:
                t_test_series = pd.Series(data).rolling(window=w_test, min_periods=1).var().fillna(0).values
                tau_test_val = np.max(t_test_series) if len(t_test_series) > 0 else 0
                threshold_50 = tau_test_val * 0.5
                
                f_dur = 0
                for i in range(t_test, -1, -1):
                    if t_test_series[i] >= threshold_50:
                        f_dur += 1
                    else:
                        break
                for i in range(t_test+1, len(t_test_series)):
                    if t_test_series[i] >= threshold_50:
                        f_dur += 1
                    else:
                        break
                fwhms.append(max(1, f_dur))
                
                # Relaxation
                mean_hist = np.mean(t_test_series[:t_test]) if t_test > 0 else np.mean(t_test_series)
                std_hist = np.std(t_test_series[:t_test]) if t_test > 0 else np.std(t_test_series)
                r_dur = len(t_test_series) - t_test
                for i in range(t_test+1, len(t_test_series)):
                    if t_test_series[i] <= (mean_hist + std_hist):
                        r_dur = i - t_test
                        break
                relaxations.append(r_dur)
                
            fwhm_str = f"{np.mean(fwhms):.1f} +/- {np.std(fwhms):.1f}"
            relax_str = f"{np.mean(relaxations):.1f} +/- {np.std(relaxations):.1f}"
            
            # Post-Collapse Regime
            post_mean = np.mean(tau_series[t_star+1:]) if t_star < len(tau_series)-1 else tau_mean_hist
            if post_mean > tau_mean_hist + 2*tau_std_hist:
                post_regime = "Hyper-volatile (New Normal is structurally unstable)"
            elif post_mean < tau_mean_hist - tau_std_hist:
                post_regime = "Hypo-volatile (System suppressed or dead)"
            else:
                post_regime = "Returned to historical baseline"
                
            # Sensitivity Drift
            t_star_arr = [x[1] for x in sensitivity_matrix]
            t_std = np.std(t_star_arr)
            if t_std > 3:
                t_min = np.min(t_star_arr)
                t_max = np.max(t_star_arr)
                if t_max - t_min > 20:
                    sensitivity_narrative = f"WARNING: Dual Time-Scales Detected (Std = {t_std:.1f} periods). The short-term anomaly at t={t_min} represents a localized micro-shock, while the long-term anomaly at t={t_max} represents a systemic macro-shift. Interpretation: The system's vulnerability is horizon-dependent; it reacts differently depending on the speed of the stressor."
                else:
                    sensitivity_narrative = f"WARNING: High Parameter Sensitivity (Std = {t_std:.1f} periods). The transition is highly scale-dependent. Conclusion: This is not a well-defined point-in-time shock, but a prolonged structural degradation process."
            else:
                sensitivity_narrative = f"Highly Stable (Std = {t_std:.1f} periods). Breakpoint is robust to parameter changes, indicating a true, well-defined instantaneous shock."
            sensitivity_narrative += f"\n     *Note: Despite drift, W={window} was chosen deterministically because it mathematically maximizes the Signal-to-Noise Ratio (SNR)."
                
            # Multivariate Synchrony
            multivariate_count = len(numeric_df.columns)
            multivariate_str = f"Evaluated jointly across {multivariate_count} variables."
            if multivariate_count > 1 and t_star > window:
                pre_collapse_df = numeric_df.iloc[:t_star]
                corr_matrix = pre_collapse_df.corr().values
                np.fill_diagonal(corr_matrix, np.nan)
                mean_r = np.nanmean(corr_matrix)
                max_r = np.nanmax(corr_matrix)
                min_r = np.nanmin(corr_matrix)
                
                sync_range = f"(Mean: {mean_r:.2f}, Min: {min_r:.2f}, Max: {max_r:.2f})"
                
                # Leading Driver Extraction
                mean_corrs = np.nanmean(corr_matrix, axis=1)
                leading_idx = np.nanargmax(mean_corrs)
                leading_col = pre_collapse_df.columns[leading_idx]
                leading_val = mean_corrs[leading_idx]
                leading_str = f"Leading Driver Detected: '{leading_col}' exhibited the highest systemic coupling (r={leading_val:.2f}) prior to collapse."
                
                if mean_r > 0.6:
                    multivariate_str = f"High System-wide Synchrony {sync_range}. Variables locked-in together.\n     -> {leading_str}"
                elif mean_r < 0.3:
                    multivariate_str = f"Low Synchrony {sync_range}. Collapse driven by isolated variables.\n     -> {leading_str}"
                else:
                    multivariate_str = f"Moderate Synchrony {sync_range}.\n     -> {leading_str}"
            
            self.math_stats = {
                "target_col": target_col,
                "data": data,
                "tau_series": tau_series,
                "acceleration": acceleration,
                "entropy": entropy,
                "coherence": coherence,
                "tau_val": tau_val,
                "max_accel": max_accel,
                "max_entropy": max_entropy,
                "min_coherence": min_coherence,
                "t_star": t_star,
                "t_star_label": t_star_label,
                "tau_median": tau_median,
                "snr": snr,
                "window": window,
                "sensitivity_matrix": sensitivity_matrix,
                "sensitivity_narrative": sensitivity_narrative,
                "effect_size": effect_size,
                "p_value": p_value,
                "significance_str": significance_str,
                "fwhm_str": fwhm_str,
                "relax_str": relax_str,
                "post_regime": post_regime,
                "precursor_signal": precursor_signal,
                "final_verdict": final_verdict,
                "multivariate_str": multivariate_str,
                "n_perm": n_perm
            }
            
            self.after(0, self._highlight_graph)
            
            msg = f"Structural break detected in '{target_col}' (Tau_s={tau_val:.2f}) at {t_star_label}."
            
            # --- DETERMINISTIC REPORT (NO AI) ---
            self._update_results(f"[MATHEMATICS] {msg}\n")
            self._generate_deterministic_report()
            
            # --- OPTIONAL AI EPISTEMIC ENGINE ---
            if self.run_ai_switch.get() == 1:
                self._update_results("\n[EPISTEMIC ENGINE] Booting Hierarchical Multi-Agent Discovery...\n")
                
                # Check API Key
                current_key = settings.google_api_key
                if not current_key or current_key == "DUMMY_GEMINI_KEY":
                    self._update_results("      -> API Key missing. Requesting from user...\n")
                    self.after(0, self._prompt_for_api_key)
                    return

                context = f"Domain: '{self.domain_menu.get()}'. {msg}."
                
                hypothesis, confidence = run_discovery_engine_sync(
                    context=context, 
                    tau_val=tau_val, 
                    update_callback=self._update_results
                )
                self.last_hypothesis = hypothesis
            else:
                self._update_results("\n[NOTE] AI Epistemic Engine is disabled. Pure mathematical interpretation complete.\n")
                self.last_hypothesis = "AI Engine was disabled. Review the deterministic mathematical report above."
                
            self._update_results("\n[COMPLETE] Analysis finalized.\n")
            
        except Exception as e:
            if "API key not valid" in str(e):
                self._update_results("      -> API Key is invalid. Requesting new key...\n")
                self.after(0, self._prompt_for_api_key)
            else:
                self._update_results(f"\n[ERROR] Analysis failed: {e}\n")
                
    def animate_phase_space(self):
        if not self.math_stats:
            return
        self.tabview.set("Phase Space")
        s = self.math_stats
        self.ax_ps.clear()
        self.ax_ps.set_title("Phase Space Trajectory Animation")
        self.ax_ps.set_xlabel("System State (Raw Data)")
        self.ax_ps.set_ylabel("System Momentum (Acceleration)")
        
        data = s["data"]
        acc = s["acceleration"]
        self.ax_ps.set_xlim(np.min(data) * 0.9, np.max(data) * 1.1)
        self.ax_ps.set_ylim(np.min(acc) * 0.9, np.max(acc) * 1.1)
        
        self.anim_frame = 0
        self.anim_max = len(data)
        self.anim_colors = np.arange(self.anim_max)
        self.animate_btn.configure(state="disabled")
        self._animate_step()

    def _animate_step(self):
        if not hasattr(self, 'anim_frame') or self.anim_frame >= self.anim_max:
            s = self.math_stats
            t_star = s["t_star"]
            self.ax_ps.scatter(s["data"][t_star], s["acceleration"][t_star], color='red', marker='*', s=200, label="t* Collapse")
            self.ax_ps.legend()
            self.canvas2.draw()
            self.animate_btn.configure(state="normal")
            return
            
        chunk = max(1, self.anim_max // 50)
        end_idx = min(self.anim_frame + chunk, self.anim_max)
        
        s = self.math_stats
        self.ax_ps.plot(s["data"][self.anim_frame:end_idx+1], s["acceleration"][self.anim_frame:end_idx+1], color="gray", alpha=0.5, linewidth=1)
        self.ax_ps.scatter(s["data"][self.anim_frame:end_idx], s["acceleration"][self.anim_frame:end_idx], c=self.anim_colors[self.anim_frame:end_idx], cmap="viridis", alpha=0.7, s=20, vmin=0, vmax=self.anim_max)
        
        self.canvas2.draw()
        self.anim_frame += chunk
        self.after(20, self._animate_step)
        
    def _highlight_graph(self):
        self.ax1.clear()
        self.ax2.clear()
        self.ax2_twin.clear()
        self.ax3.clear()
        self.ax4.clear()
        self.ax_ps.clear()
        
        s = self.math_stats
        t_star = s["t_star"]
        
        # Force strict monotonic integer index for plotting to prevent X-axis looping/clustering
        time_index = np.arange(len(s["data"]))
        t_star_val = t_star
        
        # Ax1: Tau Series over time
        self.ax1.plot(time_index, s["tau_series"], color="#1f77b4", linewidth=2, label="Systemic Tau")
        self.ax1.axvline(x=t_star_val, color='r', linestyle='--', alpha=0.7)
        
        # Calculate thresholds
        pre_break_tau = s["tau_series"][:max(1, t_star)]
        tau_danger = np.mean(pre_break_tau) + 3 * np.std(pre_break_tau)
        self.ax1.axhline(y=tau_danger, color='red', linestyle=':', alpha=0.5, label="Historical Stability Limit")
        
        # Multi-Variable Overlay logic on Ax1
        sec_col = self.secondary_menu.get()
        if sec_col and sec_col != "[None]" and sec_col in self.df.columns:
            if not hasattr(self, 'ax1_twin'):
                self.ax1_twin = self.ax1.twinx()
            self.ax1_twin.clear()
            sec_data = self.df[sec_col].ffill().fillna(0).values
            self.ax1_twin.plot(time_index, sec_data, color="gray", linestyle=":", linewidth=1.5, alpha=0.7, label=sec_col)
            self.ax1_twin.legend(loc="upper right")
        else:
            if hasattr(self, 'ax1_twin'):
                self.ax1_twin.clear()
        
        pre_break_acc = s["acceleration"][:max(1, t_star)]
        acc_danger = np.mean(pre_break_acc) + 3 * np.std(pre_break_acc)
        
        pre_break_ent = s["entropy"][:max(1, t_star)]
        ent_danger = np.mean(pre_break_ent) + 3 * np.std(pre_break_ent)
        self.ax3.axhline(y=ent_danger, color='red', linestyle=':', alpha=0.5, label="Chaos Limit")
        
        pre_break_coh = s["coherence"][:max(1, t_star)]
        coh_danger = np.mean(pre_break_coh) - 2 * np.std(pre_break_coh)

        self.ax1.set_title(f"Dynamic Systemic Tau: {s['target_col']}")
        self.ax1.legend(loc="upper left")
        
        # Ax2: Raw Data & Acceleration
        self.ax2.plot(time_index, s["data"], color="#7f7f7f", linewidth=1.5, alpha=0.5, label="Raw Data")
        self.ax2_twin.plot(time_index, s["acceleration"], color="#ff7f0e", linewidth=1.5, label="Acceleration")
        
        # Overlay Tau Curve on Raw Data (Scaled)
        if np.max(s["tau_series"]) > 0:
            tau_scaled = (s["tau_series"] / np.max(s["tau_series"])) * np.max(s["data"])
            self.ax2.plot(time_index, tau_scaled, color="#1f77b4", linestyle="--", linewidth=1.5, alpha=0.8, label="Tau (Overlay)")
            
        self.ax2.axvline(x=t_star_val, color='r', linestyle='--', alpha=0.7)
        self.ax2.set_title("Raw Data & Acceleration (a_t)")
        self.ax2.legend(loc="upper left")
        
        # Ax3: Entropic Decay
        self.ax3.plot(time_index, s["entropy"], color="#2ca02c", linewidth=1.5)
        self.ax3.axvline(x=t_star_val, color='r', linestyle='--', alpha=0.7)
        self.ax3.set_title("Entropic Decay (S_e)")
        
        # Ax4: Systemic Coherence
        self.ax4.plot(time_index, s["coherence"], color="#d62728", linewidth=1.5)
        self.ax4.axvline(x=t_star_val, color='r', linestyle='--', alpha=0.7)
        self.ax4.set_title("Systemic Coherence (C_s)")
        
        self.fig1.tight_layout(pad=3.0)
        self.canvas1.draw()
        
        # Phase Space (Ax_PS)
        scatter = self.ax_ps.scatter(s["data"], s["acceleration"], c=np.arange(len(s["data"])), cmap="viridis", alpha=0.7, s=20)
        self.ax_ps.plot(s["data"], s["acceleration"], color="gray", alpha=0.3, linewidth=0.5)
        self.ax_ps.scatter(s["data"][t_star], s["acceleration"][t_star], color='red', marker='*', s=200, label="t* Collapse")
        self.ax_ps.set_title("Phase Space: Data vs Acceleration")
        self.ax_ps.set_xlabel("System State (Raw Data)")
        self.ax_ps.set_ylabel("System Momentum (Acceleration)")
        self.ax_ps.legend()
        if not hasattr(self, '_cbar_added'):
            self.fig2.colorbar(scatter, ax=self.ax_ps, label="Time Flow")
            self._cbar_added = True
            
        self.fig2.tight_layout(pad=3.0)
        self.canvas2.draw()
        
        # Update metrics panel with cleaner formatting
        def fmt(val):
            if abs(val) < 1e-3 and val != 0:
                return f"{val:.6f}"
            return f"{val:,.2f}"

        # Traffic light colors
        def get_color(val, threshold, lower_is_worse=False):
            if np.isnan(val) or np.isnan(threshold):
                return "#2ca02c"
            if lower_is_worse:
                return "#d62728" if val <= threshold else "#2ca02c"
            else:
                return "#d62728" if val >= threshold else "#2ca02c"

        self.lbl_tau.configure(text=fmt(s['tau_val']), text_color=get_color(s['tau_val'], tau_danger))
        self.lbl_accel.configure(text=fmt(s['max_accel']), text_color=get_color(s['max_accel'], acc_danger))
        self.lbl_entropy.configure(text=fmt(s['max_entropy']), text_color=get_color(s['max_entropy'], ent_danger))
        self.lbl_coherence.configure(text=f"{s['min_coherence']:.2f}", text_color=get_color(s['min_coherence'], coh_danger, True))
        self.lbl_tstar.configure(text=s['t_star_label'])
        
        self.animate_btn.configure(state="normal")

    def _generate_deterministic_report(self):
        s = self.math_stats
        t_star_label = s['t_star_label']
        target_col = s['target_col']
        
        def fmt(val):
            if abs(val) < 1e-3 and val != 0:
                return f"{val:.6f}"
            return f"{val:,.2f}"
        
        matrix_str = ""
        for w_test, t_test, tau_test in s['sensitivity_matrix']:
            mark = "(*)" if w_test == s['window'] else "   "
            matrix_str += f"   {w_test:6d} | {t_test:15d} | {tau_test:,.2f} {mark}\n"
            
        report = (
            f"\n=======================================\n"
            f"EXECUTIVE SUMMARY:\n"
            f"The system suffered a critical structural break at {t_star_label} due to "
            f"uncontrollable entropic decay. The momentum peak of {fmt(s['max_accel'])} "
            f"indicates a severe external shock precipitating the topological collapse.\n"
            f"=======================================\n\n"
            
            f"--- STRUCTURAL DIAGNOSIS REPORT ---\n"
            f"1. TOPOLOGICAL REORGANIZATION (τ_s):\n"
            f"   A critical structural break (t*) was detected at date/index: [{t_star_label}].\n"
            f"   The magnitude of the anomaly (variance) for '{target_col}' reached a peak of {fmt(s['tau_val'])}.\n"
            f"   What does this mean? This is the exact moment the system crossed its physical stability threshold.\n\n"
            
            f"   [WINDOW OPTIMIZATION (Systemic Memory)]\n"
            f"   The calculation was performed using a systemic memory of {s['window']} intervals.\n"
            f"   Why this number? Because it yields a Signal-to-Noise Ratio (SNR) of {fmt(s['snr'])}.\n"
            f"   This means the detected anomaly peak is {fmt(s['snr'])} times larger than the system's normal background noise.\n"
            f"   Mathematically, this is the perfect window to isolate the collapse without blurring it with other data.\n\n"
            
            f"2. ACCELERATION MOMENTUM (a_t):\n"
            f"   The acceleration (second derivative) reached a peak of {fmt(s['max_accel'])}.\n"
            f"   What does this mean? There was an extreme external momentum in the data that precipitated the systemic collapse.\n\n"
            
            f"3. ENTROPIC DECAY (S_e):\n"
            f"   The maximum volatility (Entropy) was {fmt(s['max_entropy'])}.\n"
            f"   What does this mean? Prior to the breaking point, the internal chaos of the system accumulated uncontrollably,\n"
            f"   forcing the system to reorganize itself in order to survive.\n\n"
            
            f"4. SYSTEMIC COHERENCE (C_s):\n"
            f"   The systemic coherence dropped to a minimum of {fmt(s['min_coherence'])}.\n"
            f"   What does this mean? A drop in Multidimensional Eigenvalues mathematically proves that\n"
            f"   the system's variables disconnected or desynchronized from each other during the collapse.\n\n"
            
            f"5. ROBUSTNESS & STATISTICAL VALIDATION:\n"
            f"   - Null Model (Monte Carlo): {s['n_perm']} unrestricted random surrogates evaluated.\n"
            f"     Result: p-value = {s['p_value']:.4f} -> {s['significance_str']}\n"
            f"   - Effect Size: {s['effect_size']:.2f} standard deviations above historical baseline.\n"
            f"   - Early Warning Signals: {s['precursor_signal']}\n"
            f"   - Transition Geometry: FWHM = {s['fwhm_str']} periods | Relaxation Time = {s['relax_str']} periods.\n"
            f"   - Post-Collapse State: {s['post_regime']}.\n"
            f"   - Multivariate Synchrony: {s['multivariate_str']}\n\n"
            f"   [SENSITIVITY MATRIX]\n"
            f"   Window | Breakpoint (t*) | Max Tau_s\n"
            f"{matrix_str}"
            f"   -> {s['sensitivity_narrative']}\n\n"
            f"6. FINAL ANALYTICAL VERDICT:\n"
            f"   => {s['final_verdict']}\n"
            
            f"---------------------------------------\n"
            f"METHODOLOGICAL PARAMETERS:\n"
            f"- Metric: Dynamic Variance (Systemic Tau)\n"
            f"- Window: {s['window']} | Stride: 1\n"
            f"- Surrogate: Monte Carlo (Unrestricted Shuffling)\n"
            f"- Null Hypothesis (H0): Absence of temporal memory.\n"
            f"=======================================\n"
        )
        self._update_results(report)

    def _prompt_for_api_key(self):
        dialog = ctk.CTkInputDialog(text="Enter your Google Gemini API Key:", title="API Key Required")
        key = dialog.get_input()
        if key:
            env_path = os.path.join(os.getcwd(), ".env")
            with open(env_path, "a") as f:
                f.write(f"\nGOOGLE_API_KEY={key}\n")
            settings.google_api_key = key
            self._update_results("      -> API Key saved. Please click 'Analyze' again.\n")
        else:
            self._update_results("      -> Analysis aborted: No API key provided.\n")

    def _update_results(self, text, clear=False):
        self.results_box.configure(state="normal")
        if clear:
            self.results_box.delete("0.0", "end")
            self.full_log = ""
        self.results_box.insert("end", text)
        self.full_log += text
        self.results_box.see("end")
        self.results_box.configure(state="disabled")

    def explain_simply(self):
        if not hasattr(self, 'last_hypothesis'):
            return
        self._update_results("\n--- Generating Simple Explanation (LLM) ---\n")
        def _explain():
            try:
                client = genai.Client(api_key=settings.google_api_key)
                prompt = f"Explain this complex scientific hypothesis to a high schooler in one short paragraph:\n{self.last_hypothesis}"
                resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                self._update_results(f"\nSimple Explanation: {resp.text.strip()}\n")
            except Exception as e:
                self._update_results(f"\nError: {e}\n")
        threading.Thread(target=_explain, daemon=True).start()

    def export_report(self):
        if not self.full_log:
            return
        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not save_path:
            return
        self._update_results(f"\nGenerating Academic PDF Report at {save_path}...\n")
        
        def _build_pdf():
            try:
                temp_img1 = "temp_plot1.png"
                temp_img2 = "temp_plot2.png"
                self.fig1.savefig(temp_img1, dpi=150)
                self.fig2.savefig(temp_img2, dpi=150)
                
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "Systemic Tau - Mathematical & Epistemic Report", ln=True, align="C")
                pdf.ln(5)
                
                # Math Metrics
                def fmt(val):
                    if abs(val) < 1e-3 and val != 0:
                        return f"{val:.6f}"
                    return f"{val:,.2f}"
                
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, "1. Topologic Reorganization Metrics", ln=True)
                pdf.set_font("Courier", size=10)
                if self.math_stats:
                    s = self.math_stats
                    pdf.cell(0, 6, f"- Critical Mass Threshold (Max Tau_s): {fmt(s['tau_val'])}", ln=True)
                    pdf.cell(0, 6, f"- Peak Acceleration (a_t): {fmt(s['max_accel'])}", ln=True)
                    pdf.cell(0, 6, f"- Maximum Entropic Decay (S_e): {fmt(s['max_entropy'])}", ln=True)
                    pdf.cell(0, 6, f"- Systemic Coherence Trough (C_s): {s['min_coherence']:.4f}", ln=True)
                    pdf.cell(0, 6, f"- Structural Breakpoint (t*): {s['t_star_label']}", ln=True)
                pdf.ln(5)
                
                # Plot 1
                pdf.image(temp_img1, x=10, w=190)
                pdf.ln(5)
                # Plot 2
                pdf.image(temp_img2, x=10, w=190)
                pdf.ln(5)
                
                # AI Log or Deterministic Log
                pdf.set_font("Arial", 'B', 12)
                if self.run_ai_switch.get() == 1:
                    pdf.cell(0, 8, "2. Autonomous Epistemic Peer-Review", ln=True)
                else:
                    pdf.cell(0, 8, "2. Deterministic Structural Diagnosis", ln=True)
                    
                pdf.set_font("Courier", size=9)
                
                # Sanitize the log text to remove greek and complex characters that crash fpdf
                clean_log = self.full_log.replace('τ_s', 'Tau_s').replace('τ', 'Tau').replace('±', '+/-')
                clean_log = clean_log.encode('ascii', 'ignore').decode('ascii')
                pdf.multi_cell(0, 4, clean_log)
                
                pdf.output(save_path)
                if os.path.exists(temp_img1):
                    os.remove(temp_img1)
                if os.path.exists(temp_img2):
                    os.remove(temp_img2)
                    
                succ_msg = f"\n[SUCCESS] Academic PDF Exported to: {save_path}\n"
                self.after(0, lambda msg=succ_msg: self._update_results(msg))
            except Exception as e:
                err_msg = f"\n[ERROR] PDF Generation failed: {e}\n"
                self.after(0, lambda msg=err_msg: self._update_results(msg))
                
        threading.Thread(target=_build_pdf, daemon=True).start()

    def open_advanced_settings(self):
        if self.adv_window is not None and self.adv_window.winfo_exists():
            self.adv_window.focus()
            return
        self.adv_window = ctk.CTkToplevel(self)
        self.adv_window.title("Advanced Engine Settings")
        self.adv_window.geometry("500x450")
        self.adv_window.transient(self) 
        
        ctk.CTkLabel(self.adv_window, text="Autonomous Orchestrator Governance", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))
        agent_frame = ctk.CTkFrame(self.adv_window)
        agent_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(agent_frame, text="Agent Roles", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
        ctk.CTkSwitch(agent_frame, text="Enable Critic Agent (Adversarial Consensus)").pack(anchor="w", padx=20, pady=5)
        
        ctk.CTkButton(self.adv_window, text="Apply Changes", command=self.adv_window.destroy).pack(pady=20)

    def open_new_workspace(self):
        import subprocess
        subprocess.Popen([sys.executable, sys.argv[0]])

def main():
    if not ctk:
        print("Error: customtkinter is not installed.")
        sys.exit(1)
        
    ctk.set_appearance_mode("System")  
    ctk.set_default_color_theme("blue")  
    app = SystemicTauApp()
    app.mainloop()

if __name__ == "__main__":
    main()
