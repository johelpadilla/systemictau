import os
import sys
import threading
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

        self.title("Systemic Tau v8.0 - Scientific Workstation")
        self.geometry("1300x800")
        
        # Grid layout: Sidebar (col 0), Main (col 1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.adv_window = None
        self.loaded_file_path = None
        self.full_log = ""
        self.df = None
        
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
        
        # Drag and Drop Label Indicator
        if HAS_DND:
            self.dnd_label = ctk.CTkLabel(self.sidebar_frame, text="[Drag & Drop Active]", text_color="green", font=ctk.CTkFont(size=10))
            self.dnd_label.grid(row=4, column=0, padx=20, pady=5)
            # Bind DND to entire window
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.handle_dnd)
            
        self.advanced_btn = ctk.CTkButton(self.sidebar_frame, text="Advanced Settings", state="disabled", command=self.open_advanced_settings)
        self.advanced_btn.grid(row=5, column=0, padx=20, pady=20, sticky="s")

        # -------------------------------------
        # MAIN FRAME
        # -------------------------------------
        self.main_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=3) # Graph space
        self.main_frame.grid_rowconfigure(2, weight=2) # Text space
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Top bar: Upload & Analyze
        self.top_bar = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.upload_btn = ctk.CTkButton(self.top_bar, text="Select CSV/Excel File", command=self.upload_file_dialog, height=40)
        self.upload_btn.pack(side="left", padx=(0, 10))
        
        self.analyze_btn = ctk.CTkButton(self.top_bar, text="Analyze Systemic Transition", command=self.analyze_data, height=40, font=ctk.CTkFont(weight="bold"))
        self.analyze_btn.pack(side="left", padx=10)
        
        self.file_label = ctk.CTkLabel(self.top_bar, text="No file loaded.")
        self.file_label.pack(side="left", padx=20)
        
        # Middle: Matplotlib Graph Canvas
        self.graph_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.graph_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        
        # Initial empty graph
        self.fig = Figure(figsize=(8, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Systemic Data Visualization")
        self.ax.set_xlabel("Time / Index")
        self.ax.set_ylabel("Magnitude")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Bottom: Results Textbox & Export
        self.bottom_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, sticky="nsew", pady=10)
        self.bottom_frame.grid_rowconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        
        self.results_box = ctk.CTkTextbox(self.bottom_frame, font=ctk.CTkFont(family="Courier", size=12))
        self.results_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.results_box.insert("0.0", "Epistemic Engine Output Log...")
        self.results_box.configure(state="disabled")
        
        self.actions_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.actions_frame.grid(row=0, column=1, sticky="n")
        
        self.explain_btn = ctk.CTkButton(self.actions_frame, text="Explain Simply", command=self.explain_simply)
        self.explain_btn.pack(pady=10)
        
        self.export_btn = ctk.CTkButton(self.actions_frame, text="Export PDF Report", command=self.export_report)
        self.export_btn.pack(pady=10)

    def toggle_mode(self):
        if self.simple_mode_switch.get() == 1:
            self.advanced_btn.configure(state="disabled")
            if self.adv_window is not None and self.adv_window.winfo_exists():
                self.adv_window.destroy()
        else:
            self.advanced_btn.configure(state="normal")
            
    def handle_dnd(self, event):
        # tkinterdnd2 surrounds paths with curly braces if they contain spaces
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
        
        # Attempt to read and plot immediately
        try:
            if file_path.endswith('.csv'):
                self.df = pd.read_csv(file_path)
            else:
                self.df = pd.read_excel(file_path)
                
            numeric_cols = self.df.select_dtypes(include='number').columns
            if len(numeric_cols) > 0:
                self.ax.clear()
                # Plot the first numeric column as a preview
                self.ax.plot(self.df[numeric_cols[0]].values, color="#1f77b4", linewidth=2)
                self.ax.set_title(f"Preview: {numeric_cols[0]}")
                self.ax.set_xlabel("Index")
                self.ax.set_ylabel(numeric_cols[0])
                self.canvas.draw()
        except Exception as e:
            self.file_label.configure(text=f"Error reading file: {e}")
            
    def analyze_data(self):
        if not self.loaded_file_path or self.df is None:
            self._update_results("Error: Please upload a valid data file first.\\n", clear=True)
            return
            
        self.full_log = ""
        self._update_results("Initializing Systemic Tau Analysis...\\n\\n", clear=True)
        
        threading.Thread(target=self._run_real_analysis_pipeline, daemon=True).start()

    def _run_real_analysis_pipeline(self):
        try:
            numeric_df = self.df.select_dtypes(include='number')
            if numeric_df.empty:
                raise ValueError("No numeric columns found in data.")
                
            # Find the most anomalous column (highest variance / magnitude proxy)
            target_col = numeric_df.var().idxmax()
            tau_val = numeric_df[target_col].var()
            msg = f"Structural break detected in '{target_col}' (Tau_s={tau_val:.2f})"
            
            # Update Graph safely
            self.after(0, self._highlight_graph, target_col)
            
            self._update_results(f"[MATHEMATICS] {msg}\\n")
            self._update_results("\\n[EPISTEMIC ENGINE] Booting Hierarchical Multi-Agent Discovery...\\n")
            
            # Check API Key
            current_key = settings.google_api_key
            if not current_key or current_key == "DUMMY_GEMINI_KEY":
                self._update_results("      -> API Key missing. Requesting from user...\\n")
                self.after(0, self._prompt_for_api_key)
                return

            context = f"Domain: '{self.domain_menu.get()}'. {msg}."
            
            # Run Epistemic Engine
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
                self._update_results(f"\\n[ERROR] Agent Engine failed: {e}\\n")
                
    def _highlight_graph(self, col_name):
        self.ax.clear()
        data = self.df[col_name].values
        self.ax.plot(data, color="#ff7f0e", linewidth=2, label=f"Tau_s Anomaly ({col_name})")
        self.ax.set_title(f"Systemic Structural Reorganization: {col_name}")
        self.ax.set_xlabel("Time / Sequence")
        self.ax.legend()
        self.canvas.draw()

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
                # Save plot to temp file
                temp_img = "temp_plot.png"
                self.fig.savefig(temp_img)
                
                # Build PDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "Systemic Tau - Discovery Engine Report", ln=True, align="C")
                pdf.ln(5)
                
                # Insert Plot
                pdf.image(temp_img, x=10, w=190)
                pdf.ln(5)
                
                # Insert Log
                pdf.set_font("Courier", size=10)
                # Convert tricky unicode to ascii or use a font that supports it, 
                # but for simplicity encode/decode
                clean_log = self.full_log.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 5, clean_log)
                
                pdf.output(save_path)
                
                # Clean temp img
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
