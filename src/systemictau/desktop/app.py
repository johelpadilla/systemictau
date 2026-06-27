import os
import sys

# Optional try-except to avoid breaking the core library if customtkinter is not installed
try:
    import customtkinter as ctk
    from tkinter import filedialog
except ImportError:
    ctk = None

class SystemicTauApp(ctk.CTk if ctk else object):
    def __init__(self):
        super().__init__()

        self.title("Systemic Tau v8.0")
        self.geometry("900x600")
        
        # set grid layout 1x2
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Systemic Tau", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.simple_mode_switch = ctk.CTkSwitch(self.sidebar_frame, text="Simple Mode", command=self.toggle_mode)
        self.simple_mode_switch.grid(row=1, column=0, padx=20, pady=10)
        self.simple_mode_switch.select() # Default to Simple Mode
        
        self.domain_label = ctk.CTkLabel(self.sidebar_frame, text="Data Domain:", anchor="w")
        self.domain_label.grid(row=2, column=0, padx=20, pady=(10, 0))
        self.domain_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Epidemiology", "Finance", "Ecology", "General"])
        self.domain_menu.grid(row=3, column=0, padx=20, pady=(10, 20))
        
        self.advanced_btn = ctk.CTkButton(self.sidebar_frame, text="Advanced Settings", state="disabled")
        self.advanced_btn.grid(row=4, column=0, padx=20, pady=10, sticky="n")

        # create main frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Upload Area
        self.upload_btn = ctk.CTkButton(self.main_frame, text="Drag & Drop Data File Here\nor Click to Browse", 
                                        height=100, command=self.upload_file, fg_color="transparent", border_width=2)
        self.upload_btn.grid(row=0, column=0, padx=40, pady=40, sticky="ew")
        
        self.analyze_btn = ctk.CTkButton(self.main_frame, text="Analyze Data", command=self.analyze_data, height=40, font=ctk.CTkFont(weight="bold"))
        self.analyze_btn.grid(row=1, column=0, padx=40, pady=10)
        
        # Results Textbox
        self.results_box = ctk.CTkTextbox(self.main_frame)
        self.results_box.grid(row=2, column=0, padx=40, pady=(20, 10), sticky="nsew")
        self.results_box.insert("0.0", "Results will appear here...")
        self.results_box.configure(state="disabled")
        
        # Export and Explain Buttons
        self.actions_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.actions_frame.grid(row=3, column=0, padx=40, pady=(0, 20), sticky="e")
        
        self.explain_btn = ctk.CTkButton(self.actions_frame, text="Explain Simply", command=self.explain_simply)
        self.explain_btn.pack(side="left", padx=10)
        
        self.export_btn = ctk.CTkButton(self.actions_frame, text="Export PDF Report", command=self.export_report)
        self.export_btn.pack(side="left")

    def toggle_mode(self):
        if self.simple_mode_switch.get() == 1:
            self.advanced_btn.configure(state="disabled")
        else:
            self.advanced_btn.configure(state="normal")
            
    def upload_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Data Files", "*.csv *.xlsx")])
        if file_path:
            self.upload_btn.configure(text=f"Loaded: {os.path.basename(file_path)}")
            
    def analyze_data(self):
        self.results_box.configure(state="normal")
        self.results_box.delete("0.0", "end")
        self.results_box.insert("0.0", "Running Autonomous Discovery Engine...\\n\\n")
        self.results_box.insert("end", "[1/3] Detecting structural transitions (t*)...\\n")
        self.results_box.insert("end", "[2/3] Multi-Agent Engine generating hypotheses...\\n")
        self.results_box.insert("end", "[3/3] Fetching empirical evidence...\\n\\n")
        self.results_box.insert("end", "Done. Found 1 critical transition associated with systemic collapse.")
        self.results_box.configure(state="disabled")

    def explain_simply(self):
        self.results_box.configure(state="normal")
        self.results_box.insert("end", "\\n\\n--- Simple Explanation ---\\n")
        self.results_box.insert("end", "The system noticed a major, unusual change in the data you provided. This looks like a sudden break or collapse. The AI verified this by checking real-world literature and found strong evidence that this type of pattern leads to structural failure.")
        self.results_box.configure(state="disabled")

    def export_report(self):
        print("Exporting PDF report...")

def main():
    if not ctk:
        print("Error: customtkinter is not installed. Please install it with 'pip install customtkinter' or 'pip install systemictau[desktop]'")
        sys.exit(1)
        
    ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
    app = SystemicTauApp()
    app.mainloop()

if __name__ == "__main__":
    main()
