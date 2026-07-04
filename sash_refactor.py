import re

with open('src/systemictau/desktop/app.py', 'r') as f:
    content = f.read()

# 1. Update the grid column configuration
old_grid_conf = """        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)"""
new_grid_conf = """        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)"""
content = content.replace(old_grid_conf, new_grid_conf)

# 2. Update sidebar definition
old_sidebar = """        # -------------------------------------
        self.sidebar_frame = ctk.CTkScrollableFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(15, weight=1)"""
new_sidebar = """        # -------------------------------------
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid_rowconfigure(1, weight=1)
        
        self.sash = ctk.CTkFrame(self, width=4, corner_radius=0, fg_color="gray30", cursor="sb_h_double_arrow")
        self.sash.grid(row=0, column=1, sticky="ns")
        self.sash.bind("<B1-Motion>", self._resize_sidebar)"""
content = content.replace(old_sidebar, new_sidebar)

# 3. Add _resize_sidebar inside the class methods
# Let's add it right after __init__
resize_method = """
    def _resize_sidebar(self, event):
        new_width = event.x_root - self.winfo_rootx()
        if new_width < 200: new_width = 200
        if new_width > 600: new_width = 600
        self.sidebar_frame.configure(width=new_width)
"""
# Find "def enter(self, event=None):" which is the first method in some classes, wait, in SystemicTauApp __init__ ends around line 480.
# We can just append it at the end of the file, inside the class SystemicTauApp.
# Actually, I can insert it right before "def _show_coming_soon"
content = content.replace("    def _show_coming_soon(self):", resize_method + "\n    def _show_coming_soon(self):")

# 4. Move main_frame to column 2
old_main = """        self.main_frame = ctk.CTkScrollableFrame(self, corner_radius=10, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")"""
new_main = """        self.main_frame = ctk.CTkScrollableFrame(self, corner_radius=10, fg_color="transparent")
        self.main_frame.grid(row=0, column=2, padx=20, pady=20, sticky="nsew")"""
content = content.replace(old_main, new_main)

with open('src/systemictau/desktop/app.py', 'w') as f:
    f.write(content)
print("Sash applied")
