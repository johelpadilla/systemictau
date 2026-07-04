import pandas as pd
from systemictau.desktop.app import SystemicTauApp

app = SystemicTauApp()
# Mock data
app.df = pd.DataFrame({"total_cases": [1, 2, 3, 10, 50, 100, 5]})
app.loaded_file_path = "dummy.csv"
app.target_menu.set("total_cases")
app._run_real_analysis_pipeline()
print("Success!")
