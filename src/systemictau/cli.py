import typer
import pickle
from pathlib import Path
from typing import Optional

# Ensure user has installed full extras before importing data/viz
try:
    import pandas as pd
    from systemictau.data import from_dataframe
    from systemictau.visualization import plot_tau_evolution
except ImportError:
    raise ImportError("CLI requires the 'full' installation. Run 'pip install systemictau[full]'")

app = typer.Typer(help="Systemic Tau Command Line Interface")

@app.command()
def analyze(
    data_path: Path = typer.Argument(..., help="Path to input CSV data file"),
    output: Path = typer.Option(..., "--output", "-o", help="Path to save the output SystemicTauResult (.pkl)"),
    time_col: Optional[str] = typer.Option(None, "--time-col", "-t", help="Column name to use as time/index"),
    window_size: int = typer.Option(13, "--window", "-w", help="Size of the sliding window"),
    imputation: str = typer.Option('linear', "--imputation", "-i", help="Missing data handling ('linear', 'ffill', 'drop')")
):
    """
    Computes Systemic Tau from a CSV dataset and saves the result to a pickle file.
    """
    if not data_path.exists():
        typer.secho(f"Error: File {data_path} not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
        
    typer.secho(f"Loading data from {data_path}...", fg=typer.colors.CYAN)
    df = pd.read_csv(data_path)
    
    typer.secho(f"Computing Systemic Tau (window={window_size}, imputation={imputation})...", fg=typer.colors.CYAN)
    result = from_dataframe(df, time_col=time_col, window_size=window_size, imputation=imputation)
    
    # Save result using pickle
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'wb') as f:
        pickle.dump(result, f)
        
    typer.secho(f"Success! Result saved to {output}", fg=typer.colors.GREEN)

@app.command()
def plot(
    result_path: Path = typer.Argument(..., help="Path to the saved SystemicTauResult (.pkl)"),
    plot_type: str = typer.Option('tau_evolution', "--type", help="Type of plot: 'tau_evolution'")
):
    """
    Plots results from a previously computed SystemicTauResult.
    """
    if not result_path.exists():
        typer.secho(f"Error: File {result_path} not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
        
    with open(result_path, 'rb') as f:
        result = pickle.load(f)
        
    import matplotlib.pyplot as plt
    
    if plot_type == 'tau_evolution':
        typer.secho("Generating Systemic Tau Evolution plot...", fg=typer.colors.CYAN)
        plot_tau_evolution(result.taus_global)
        plt.show()
    else:
        typer.secho(f"Error: Unknown plot type '{plot_type}'", fg=typer.colors.RED)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
