import os
import sys
import threading
import numpy as np
import pandas as pd
from google import genai
from systemictau.config import settings
from systemictau.agents.epistemic_engine import run_discovery_engine_sync

try:
    from fpdf import FPDF
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
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
        self.domain_menu.grid(row=3, column=0, padx=20, pady=(10, 20))
        
        if HAS_DND:
            self.dnd_label = ctk.CTkLabel(self.sidebar_frame, text="[Drag & Drop Active]", text_color="green", font=ctk.CTkFont(size=10))
            self.dnd_label.grid(row=4, column=0, padx=20, pady=5)
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.handle_dnd)
            
        self.advanced_btn = ctk.CTkButton(self.sidebar_frame, text="Advanced Settings", state="disabled", command=self.open_advanced_settings)
        self.advanced_btn.grid(row=5, column=0, padx=20, pady=20, sticky="s")

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
        
        # Middle: Matplotlib 2x2 Grid
        self.graph_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.graph_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        
        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.ax1 = self.fig.add_subplot(221)
        self.ax2 = self.fig.add_subplot(222)
        self.ax3 = self.fig.add_subplot(223)
        self.ax4 = self.fig.add_subplot(224)
        self.fig.tight_layout(pad=3.0)
        
        self.ax1.set_title("Systemic Tau (τ_s) - Magnitude")
        self.ax2.set_title("Acceleration (a_t)")
        self.ax3.set_title("Entropic Decay (S_e)")
        self.ax4.set_title("Systemic Coherence (C_s)")
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Bottom: Metrics & AI Log
        self.bottom_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, sticky="nsew", pady=10)
        self.bottom_frame.grid_rowconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(0, weight=1) # Metrics
        self.bottom_frame.grid_columnconfigure(1, weight=3) # Log
        self.bottom_frame.grid_columnconfigure(2, weight=0) # Buttons
        
        # Math Metrics Panel
        self.metrics_frame = ctk.CTkFrame(self.bottom_frame)
        self.metrics_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(self.metrics_frame, text="HARD METRICS", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.lbl_tau = ctk.CTkLabel(self.metrics_frame, text="Max τ_s: --")
        self.lbl_tau.pack(anchor="w", padx=10, pady=2)
        self.lbl_accel = ctk.CTkLabel(self.metrics_frame, text="Peak Accel: --")
        self.lbl_accel.pack(anchor="w", padx=10, pady=2)
        self.lbl_entropy = ctk.CTkLabel(self.metrics_frame, text="Max S_e: --")
        self.lbl_entropy.pack(anchor="w", padx=10, pady=2)
        self.lbl_coherence = ctk.CTkLabel(self.metrics_frame, text="Min C_s: --")
        self.lbl_coherence.pack(anchor="w", padx=10, pady=2)
        self.lbl_tstar = ctk.CTkLabel(self.metrics_frame, text="t* Index: --", text_color="#ff7f0e", font=ctk.CTkFont(weight="bold"))
        self.lbl_tstar.pack(anchor="w", padx=10, pady=2)

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
                
            numeric_cols = self.df.select_dtypes(include='number').columns
            if len(numeric_cols) > 0:
                self.ax1.clear(); self.ax2.clear(); self.ax3.clear(); self.ax4.clear()
                self.ax1.plot(self.df[numeric_cols[0]].values, color="#1f77b4")
                self.ax1.set_title(f"Preview: {numeric_cols[0]}")
                self.canvas.draw()
        except Exception as e:
            self.file_label.configure(text=f"Error reading file: {e}")
            
    def analyze_data(self):
        if not self.loaded_file_path or self.df is None:
            self._update_results("Error: Please upload a valid data file first.\\n", clear=True)
            return
            
        self.full_log = ""
        self._update_results("Initializing Systemic Tau Mathematical Analysis...\\n\\n", clear=True)
        threading.Thread(target=self._run_real_analysis_pipeline, daemon=True).start()

    def _run_real_analysis_pipeline(self):
        try:
            numeric_df = self.df.select_dtypes(include='number')
            if numeric_df.empty:
                raise ValueError("No numeric columns found in data.")
                
            # --- MATHEMATICAL ENGINE ---
            target_col = numeric_df.var().idxmax()
            data = numeric_df[target_col].values
            
            # 1. Systemic Tau (Raw Magnitude)
            tau_val = np.var(data)
            t_star = np.argmax(data)
            
            # 2. Acceleration (Second Derivative)
            velocity = np.gradient(data)
            acceleration = np.gradient(velocity)
            max_accel = np.max(acceleration)
            
            # 3. Entropic Decay (Rolling Volatility Proxy)
            window = max(3, len(data) // 20)
            entropy = pd.Series(data).rolling(window=window, min_periods=1).std().values
            max_entropy = np.nanmax(entropy)
            
            # 4. Systemic Coherence (Rolling Correlation)
            if len(numeric_df.columns) > 1:
                second_col = numeric_df.drop(columns=[target_col]).var().idxmax()
                coherence = pd.Series(data).rolling(window=window, min_periods=1).corr(numeric_df[second_col]).fillna(0).values
            else:
                # Autocorrelation proxy if only 1 column
                coherence = pd.Series(data).rolling(window=window, min_periods=1).corr(pd.Series(data).shift(1)).fillna(0).values
            min_coherence = np.nanmin(coherence)
            
            self.math_stats = {
                "target_col": target_col,
                "data": data,
                "acceleration": acceleration,
                "entropy": entropy,
                "coherence": coherence,
                "tau_val": tau_val,
                "max_accel": max_accel,
                "max_entropy": max_entropy,
                "min_coherence": min_coherence,
                "t_star": t_star
            }
            
            self.after(0, self._highlight_graph)
            
            msg = f"Structural break detected in '{target_col}' (Tau_s={tau_val:.2f}) at index {t_star}."
            self._update_results(f"[MATHEMATICS] {msg}\\n")
            self._update_results("\\n[EPISTEMIC ENGINE] Booting Hierarchical Multi-Agent Discovery...\\n")
            
            # Check API Key
            current_key = settings.google_api_key
            if not current_key or current_key == "DUMMY_GEMINI_KEY":
                self._update_results("      -> API Key missing. Requesting from user...\\n")
                self.after(0, self._prompt_for_api_key)
                return

            context = f"Domain: '{self.domain_menu.get()}'. {msg}."
            
            hypothesis, confidence = run_discovery_engine_sync(
                context=context, 
                tau_val=tau_val, 
                update_callback=self._update_results
            )
            
            self._update_results("\\n[COMPLETE] Autonomous analysis finalized.\\n")
            self.last_hypothesis = hypothesis
            
        except Exception as e:
            if "API key not valid" in str(e):
                self._update_results("      -> API Key is invalid. Requesting new key...\\n")
                self.after(0, self._prompt_for_api_key)
            else:
                self._update_results(f"\\n[ERROR] Analysis failed: {e}\\n")
                
    def _highlight_graph(self):
        self.ax1.clear(); self.ax2.clear(); self.ax3.clear(); self.ax4.clear()
        
        s = self.math_stats
        t_star = s["t_star"]
        
        # Ax1: Tau Magnitude
        self.ax1.plot(s["data"], color="#1f77b4", linewidth=2)
        self.ax1.axvline(x=t_star, color='r', linestyle='--', alpha=0.7)
        self.ax1.set_title(f"Systemic Tau (Magnitude): {s['target_col']}")
        
        # Ax2: Acceleration
        self.ax2.plot(s["acceleration"], color="#ff7f0e", linewidth=1.5)
        self.ax2.axvline(x=t_star, color='r', linestyle='--', alpha=0.7)
        self.ax2.set_title("Acceleration (a_t)")
        
        # Ax3: Entropic Decay
        self.ax3.plot(s["entropy"], color="#2ca02c", linewidth=1.5)
        self.ax3.axvline(x=t_star, color='r', linestyle='--', alpha=0.7)
        self.ax3.set_title("Entropic Decay (S_e)")
        
        # Ax4: Systemic Coherence
        self.ax4.plot(s["coherence"], color="#d62728", linewidth=1.5)
        self.ax4.axvline(x=t_star, color='r', linestyle='--', alpha=0.7)
        self.ax4.set_title("Systemic Coherence (C_s)")
        
        self.fig.tight_layout(pad=3.0)
        self.canvas.draw()
        
        # Update metrics panel
        self.lbl_tau.configure(text=f"Max τ_s: {s['tau_val']:.2e}")
        self.lbl_accel.configure(text=f"Peak Accel: {s['max_accel']:.2e}")
        self.lbl_entropy.configure(text=f"Max S_e: {s['max_entropy']:.2e}")
        self.lbl_coherence.configure(text=f"Min C_s: {s['min_coherence']:.2f}")
        self.lbl_tstar.configure(text=f"t* Index: {t_star}")

    def _prompt_for_api_key(self):
        dialog = ctk.CTkInputDialog(text="Enter your Google Gemini API Key:", title="API Key Required")
        key = dialog.get_input()
        if key:
            env_path = os.path.join(os.getcwd(), ".env")
            with open(env_path, "a") as f:
                f.write(f"\\nGOOGLE_API_KEY={key}\\n")
            settings.google_api_key = key
            self._update_results("      -> API Key saved. Please click 'Analyze' again.\\n")
        else:
            self._update_results("      -> Analysis aborted: No API key provided.\\n")

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
        self._update_results("\\n--- Generating Simple Explanation (LLM) ---\\n")
        def _explain():
            try:
                client = genai.Client(api_key=settings.google_api_key)
                prompt = f"Explain this complex scientific hypothesis to a high schooler in one short paragraph:\\n{self.last_hypothesis}"
                resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                self._update_results(f"\\nSimple Explanation: {resp.text.strip()}\\n")
            except Exception as e:
                self._update_results(f"\\nError: {e}\\n")
        threading.Thread(target=_explain, daemon=True).start()

    def export_report(self):
        if not self.full_log:
            return
        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not save_path:
            return
        self._update_results(f"\\nGenerating Academic PDF Report at {save_path}...\\n")
        
        def _build_pdf():
            try:
                temp_img = "temp_plot.png"
                self.fig.savefig(temp_img, dpi=150)
                
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "Systemic Tau - Mathematical & Epistemic Report", ln=True, align="C")
                pdf.ln(5)
                
                # Math Metrics
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, "1. Topologic Reorganization Metrics", ln=True)
                pdf.set_font("Courier", size=10)
                if self.math_stats:
                    s = self.math_stats
                    pdf.cell(0, 6, f"- Critical Mass Threshold (Max τ_s): {s['tau_val']:.4e}", ln=True)
                    pdf.cell(0, 6, f"- Peak Acceleration (a_t): {s['max_accel']:.4e}", ln=True)
                    pdf.cell(0, 6, f"- Maximum Entropic Decay (S_e): {s['max_entropy']:.4e}", ln=True)
                    pdf.cell(0, 6, f"- Systemic Coherence Trough (C_s): {s['min_coherence']:.4f}", ln=True)
                    pdf.cell(0, 6, f"- Structural Breakpoint (t*): Index {s['t_star']}", ln=True)
                pdf.ln(5)
                
                # Plot
                pdf.image(temp_img, x=10, w=190)
                pdf.ln(5)
                
                # AI Log
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, "2. Autonomous Epistemic Peer-Review", ln=True)
                pdf.set_font("Courier", size=9)
                clean_log = self.full_log.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 4, clean_log)
                
                pdf.output(save_path)
                if os.path.exists(temp_img):
                    os.remove(temp_img)
                    
                self.after(0, lambda: self._update_results(f"\\n[SUCCESS] PDF Exported.\\n"))
            except Exception as e:
                self.after(0, lambda: self._update_results(f"\\n[ERROR] PDF Generation failed: {e}\\n"))
                
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
