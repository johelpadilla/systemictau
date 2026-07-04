import re

with open('src/systemictau/desktop/app.py', 'r') as f:
    content = f.read()

# We need to replace the layout code inside _setup_ui.
# Since we modified the file, let's just do a string replacement.
old_ui = """        self.simple_mode_switch = ctk.CTkSwitch(self.sidebar_frame, text="Simple Mode", command=self.toggle_mode)
        self.simple_mode_switch.grid(row=1, column=0, padx=20, pady=10)
        self.simple_mode_switch.select()
        
        # Time Variable Selection
        self.time_label = ctk.CTkLabel(self.sidebar_frame, text="Time Variable (X-Axis):", anchor="w")
        self.time_label.grid(row=2, column=0, padx=20, pady=(2, 0))
        self.time_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["[Auto Detect]"], command=lambda _: self._redraw_preview(self.target_menu.get()))
        self.time_menu.grid(row=3, column=0, padx=20, pady=(2, 2))
        
        # Data Health Strategy
        self.health_label_side = ctk.CTkLabel(self.sidebar_frame, text="Missing Data Strategy:", anchor="w")
        self.health_label_side.grid(row=4, column=0, padx=20, pady=(2, 0))
        self.health_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Prompt Me", "Auto-Interpolate", "Strict (Abort)"])
        self.health_menu.grid(row=5, column=0, padx=20, pady=(2, 2))
        
        # Ontological Scale
        self.scale_label = ctk.CTkLabel(self.sidebar_frame, text="Ontological Scale:", anchor="w", text_color="#2ca02c")
        self.scale_label.grid(row=6, column=0, padx=20, pady=(2, 0))
        self.scale_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Local", "Medium", "Global"], command=self._on_scale_change)
        self.scale_menu.grid(row=7, column=0, padx=20, pady=(2, 2))
        
        # Cluster Aggregation (Hidden by default, shown for Medium)
        self.cluster_agg_label = ctk.CTkLabel(self.sidebar_frame, text="Cluster Aggregation:", anchor="w")
        # Hidden initially
        self.cluster_agg_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Summation", "Median"])
        # Hidden initially
        
        # Target Variable Selection
        self.target_primary_label = ctk.CTkLabel(self.sidebar_frame, text="Primary Target:", anchor="w", text_color="orange")
        self.target_primary_label.grid(row=10, column=0, padx=20, pady=(2, 0))
        self.target_primary_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["[Load File First]"], command=self._redraw_preview)
        self.target_primary_menu.grid(row=11, column=0, padx=20, pady=(0, 2))

        self.target_header_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.target_header_frame.grid(row=12, column=0, padx=20, pady=(2, 0), sticky="ew")
        self.target_label = ctk.CTkLabel(self.target_header_frame, text="Secondary Variables:", anchor="w")
        self.target_label.pack(side="left")
        self.select_all_btn = ctk.CTkButton(self.target_header_frame, text="All/None", width=50, height=20, command=self.toggle_all_targets)
        self.select_all_btn.pack(side="right")
        
        self.target_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, height=80)
        self.target_scroll.grid(row=13, column=0, padx=20, pady=(0, 2), sticky="ew")
        self.target_checkboxes = {}
        
        # Secondary Variable Selection (Overlay)
        self.secondary_label = ctk.CTkLabel(self.sidebar_frame, text="Plot Overlay:", anchor="w", text_color="gray60")
        self.secondary_label.grid(row=14, column=0, padx=20, pady=(2, 0))
        self.secondary_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["[None]"], command=self.analyze_data)
        self.secondary_menu.grid(row=15, column=0, padx=20, pady=(0, 2))
        
        self.window_label = ctk.CTkLabel(self.sidebar_frame, text="Systemic Memory (Window):", anchor="w")
        self.window_label.grid(row=16, column=0, padx=20, pady=(2, 0))
        self.window_slider = ctk.CTkSlider(self.sidebar_frame, from_=3, to=100, command=self._on_slider_change)
        self.window_slider.set(20)
        self.window_slider.grid(row=17, column=0, padx=20, pady=(2, 2))
        
        self.optimize_btn = ctk.CTkButton(self.sidebar_frame, text="⚡ Auto-Optimize Window", command=self.optimize_window, fg_color="#2ca02c", hover_color="#238023")
        self.optimize_btn.grid(row=18, column=0, padx=20, pady=(0, 5))
        
        self.animate_btn = ctk.CTkButton(self.sidebar_frame, text="▶ Animate Phase Space", command=self.animate_phase_space, state="disabled", fg_color="#ff7f0e", hover_color="#d62728")
        self.animate_btn.grid(row=19, column=0, padx=20, pady=(0, 5))
        
        self.run_ai_switch = ctk.CTkSwitch(self.sidebar_frame, text="Enable AI Agents")
        self.run_ai_switch.grid(row=20, column=0, padx=20, pady=(2, 2))
        
        self.smoothing_label = ctk.CTkLabel(self.sidebar_frame, text="Signal Smoothing:", anchor="w")
        self.smoothing_label.grid(row=21, column=0, padx=20, pady=(2, 0))
        self.smoothing_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["[None]", "Moving Average (n=3)", "Savitzky-Golay (n=5)"])
        self.smoothing_menu.grid(row=22, column=0, padx=20, pady=(0, 5))
        
        # --- Geospatial Mapping UI ---
        self.geo_label = ctk.CTkLabel(self.sidebar_frame, text="Geospatial Map:", anchor="w", font=ctk.CTkFont(weight="bold"))
        self.geo_label.grid(row=23, column=0, padx=20, pady=(2, 0))
        
        self.load_coords_btn = ctk.CTkButton(self.sidebar_frame, text="📍 Load Coordinates", command=self.load_coordinates)
        self.load_coords_btn.grid(row=24, column=0, padx=20, pady=(2, 2))
        
        self.scale_markers_switch = ctk.CTkSwitch(self.sidebar_frame, text="Scale by Tau_s")
        self.scale_markers_switch.select()
        self.scale_markers_switch.grid(row=25, column=0, padx=20, pady=(0, 2))
        
        self.generate_map_btn = ctk.CTkButton(self.sidebar_frame, text="🌍 Generate Map", command=self.generate_map, state="disabled", fg_color="#1f538d", hover_color="#14375d")
        self.generate_map_btn.grid(row=26, column=0, padx=20, pady=(0, 5))
        
        if HAS_DND:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.handle_dnd)
            
        # Session and Settings Buttons
        self.session_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.session_frame.grid(row=27, column=0, padx=20, pady=(2, 2), sticky="s")
        
        self.save_btn = ctk.CTkButton(self.session_frame, text="💾 Save Session", width=90, command=self.save_session)
        self.save_btn.pack(side="left", padx=2)
        
        self.load_btn = ctk.CTkButton(self.session_frame, text="📂 Load", width=60, command=self.load_session)
        self.load_btn.pack(side="left", padx=2)
        
        self.settings_btn = ctk.CTkButton(self.sidebar_frame, text="⚙️ Settings", command=self.open_settings)
        self.settings_btn.grid(row=28, column=0, padx=20, pady=(2, 2), sticky="s")
        
        # Push to bottom
        self.sidebar_frame.grid_rowconfigure(26, weight=0)
        self.sidebar_frame.grid_rowconfigure(27, weight=1)
        self.sidebar_frame.grid_rowconfigure(28, weight=0)"""

new_ui = """        self.sidebar_tabs = ctk.CTkTabview(self.sidebar_frame, width=200)
        self.sidebar_tabs.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(1, weight=1)
        
        self.tab_data = self.sidebar_tabs.add("Data")
        self.tab_analysis = self.sidebar_tabs.add("Analysis")
        self.tab_tools = self.sidebar_tabs.add("Tools")
        
        # --- TAB: DATA ---
        self.time_label = ctk.CTkLabel(self.tab_data, text="Time Variable (X-Axis):", anchor="w")
        self.time_label.pack(anchor="w", padx=10, pady=(5, 0))
        self.time_menu = ctk.CTkOptionMenu(self.tab_data, values=["[Auto Detect]"], command=lambda _: self._redraw_preview(self.target_menu.get() if hasattr(self, 'target_menu') else None))
        self.time_menu.pack(fill="x", padx=10, pady=(0, 5))
        
        self.health_label_side = ctk.CTkLabel(self.tab_data, text="Missing Data Strategy:", anchor="w")
        self.health_label_side.pack(anchor="w", padx=10, pady=(5, 0))
        self.health_menu = ctk.CTkOptionMenu(self.tab_data, values=["Prompt Me", "Auto-Interpolate", "Strict (Abort)"])
        self.health_menu.pack(fill="x", padx=10, pady=(0, 5))
        
        self.scale_label = ctk.CTkLabel(self.tab_data, text="Ontological Scale:", anchor="w", text_color="#2ca02c")
        self.scale_label.pack(anchor="w", padx=10, pady=(5, 0))
        self.scale_menu = ctk.CTkOptionMenu(self.tab_data, values=["Local", "Medium", "Global"], command=self._on_scale_change)
        self.scale_menu.pack(fill="x", padx=10, pady=(0, 5))
        
        self.cluster_agg_label = ctk.CTkLabel(self.tab_data, text="Cluster Aggregation:", anchor="w")
        self.cluster_agg_menu = ctk.CTkOptionMenu(self.tab_data, values=["Summation", "Median"])
        
        self.target_primary_label = ctk.CTkLabel(self.tab_data, text="Primary Target:", anchor="w", text_color="orange")
        self.target_primary_label.pack(anchor="w", padx=10, pady=(5, 0))
        self.target_primary_menu = ctk.CTkOptionMenu(self.tab_data, values=["[Load File First]"], command=self._redraw_preview)
        self.target_primary_menu.pack(fill="x", padx=10, pady=(0, 5))

        self.target_header_frame = ctk.CTkFrame(self.tab_data, fg_color="transparent")
        self.target_header_frame.pack(fill="x", padx=10, pady=(5, 0))
        self.target_label = ctk.CTkLabel(self.target_header_frame, text="Secondary Variables:", anchor="w")
        self.target_label.pack(side="left")
        self.select_all_btn = ctk.CTkButton(self.target_header_frame, text="All/None", width=50, height=20, command=self.toggle_all_targets)
        self.select_all_btn.pack(side="right")
        
        self.target_scroll = ctk.CTkScrollableFrame(self.tab_data, height=120)
        self.target_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        self.target_checkboxes = {}
        
        # --- TAB: ANALYSIS ---
        self.simple_mode_switch = ctk.CTkSwitch(self.tab_analysis, text="Simple Mode", command=self.toggle_mode)
        self.simple_mode_switch.pack(padx=10, pady=10)
        self.simple_mode_switch.select()
        
        self.secondary_label = ctk.CTkLabel(self.tab_analysis, text="Plot Overlay:", anchor="w", text_color="gray60")
        self.secondary_label.pack(anchor="w", padx=10, pady=(5, 0))
        self.secondary_menu = ctk.CTkOptionMenu(self.tab_analysis, values=["[None]"], command=self.analyze_data)
        self.secondary_menu.pack(fill="x", padx=10, pady=(0, 5))
        
        self.window_label = ctk.CTkLabel(self.tab_analysis, text="Systemic Memory (Window):", anchor="w")
        self.window_label.pack(anchor="w", padx=10, pady=(5, 0))
        self.window_slider = ctk.CTkSlider(self.tab_analysis, from_=3, to=100, command=self._on_slider_change)
        self.window_slider.set(20)
        self.window_slider.pack(fill="x", padx=10, pady=(5, 5))
        
        self.optimize_btn = ctk.CTkButton(self.tab_analysis, text="⚡ Auto-Optimize Window", command=self.optimize_window, fg_color="#2ca02c", hover_color="#238023")
        self.optimize_btn.pack(fill="x", padx=10, pady=(5, 5))
        
        self.animate_btn = ctk.CTkButton(self.tab_analysis, text="▶ Animate Phase Space", command=self.animate_phase_space, state="disabled", fg_color="#ff7f0e", hover_color="#d62728")
        self.animate_btn.pack(fill="x", padx=10, pady=(5, 5))
        
        self.run_ai_switch = ctk.CTkSwitch(self.tab_analysis, text="Enable AI Agents")
        self.run_ai_switch.pack(padx=10, pady=10)
        
        self.smoothing_label = ctk.CTkLabel(self.tab_analysis, text="Signal Smoothing:", anchor="w")
        self.smoothing_label.pack(anchor="w", padx=10, pady=(5, 0))
        self.smoothing_menu = ctk.CTkOptionMenu(self.tab_analysis, values=["[None]", "Moving Average (n=3)", "Savitzky-Golay (n=5)"])
        self.smoothing_menu.pack(fill="x", padx=10, pady=(0, 5))
        
        # --- TAB: TOOLS ---
        self.geo_label = ctk.CTkLabel(self.tab_tools, text="Geospatial Map:", anchor="w", font=ctk.CTkFont(weight="bold"))
        self.geo_label.pack(anchor="w", padx=10, pady=(5, 0))
        self.load_coords_btn = ctk.CTkButton(self.tab_tools, text="📍 Load Coordinates", command=self.load_coordinates)
        self.load_coords_btn.pack(fill="x", padx=10, pady=5)
        self.scale_markers_switch = ctk.CTkSwitch(self.tab_tools, text="Scale by Tau_s")
        self.scale_markers_switch.select()
        self.scale_markers_switch.pack(padx=10, pady=5)
        self.generate_map_btn = ctk.CTkButton(self.tab_tools, text="🌍 Generate Map", command=self.generate_map, state="disabled", fg_color="#1f538d", hover_color="#14375d")
        self.generate_map_btn.pack(fill="x", padx=10, pady=5)
        
        self.session_frame = ctk.CTkFrame(self.tab_tools, fg_color="transparent")
        self.session_frame.pack(fill="x", padx=10, pady=10)
        self.save_btn = ctk.CTkButton(self.session_frame, text="💾 Save", width=60, command=self.save_session)
        self.save_btn.pack(side="left", padx=2, expand=True)
        self.load_btn = ctk.CTkButton(self.session_frame, text="📂 Load", width=60, command=self.load_session)
        self.load_btn.pack(side="left", padx=2, expand=True)
        
        self.settings_btn = ctk.CTkButton(self.tab_tools, text="⚙️ Settings", command=self.open_settings)
        self.settings_btn.pack(fill="x", padx=10, pady=5)
        
        if HAS_DND:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.handle_dnd)"""

content = content.replace(old_ui, new_ui)

with open('src/systemictau/desktop/app.py', 'w') as f:
    f.write(content)
print("Tabview replacement injected")
