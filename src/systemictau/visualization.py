import numpy as np

def _check_matplotlib():
    """Helper to check if matplotlib is installed since it's an optional dependency."""
    try:
        import matplotlib.pyplot as plt
        return plt
    except ImportError:
        raise ImportError(
            "The visualization module requires matplotlib. "
            "Install it via 'pip install systemictau[visualization]' or 'pip install matplotlib'."
        )

def plot_tau_evolution(taus_global, T_series=None, episodes=None, ax=None):
    """
    Plots the evolution of Systemic Tau and optionally the RECD T_series and Joint Episodes.
    """
    plt = _check_matplotlib()
    
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 4))
        
    t = np.arange(len(taus_global))
    ax.plot(t, taus_global, color='blue', label='Systemic Tau', alpha=0.7)
    
    # Plot T_series on secondary y-axis if provided
    if T_series is not None:
        ax2 = ax.twinx()
        ax2.plot(t, T_series, color='red', label='T (RECD)', linewidth=2)
        ax2.set_ylabel("Discrete Time $T$")
        ax2.legend(loc="upper right")
        
    # Highlight joint episodes if provided
    if episodes is not None:
        for ep in episodes:
            ax.axvspan(ep['start'], ep['end'], color='yellow', alpha=0.3, 
                       label='Joint Episode' if ep == episodes[0] else "")
            
    ax.axhline(y=0.41, color='green', linestyle='--', label='Chaos Threshold (0.41)')
    ax.axhline(y=0.50, color='black', linestyle='--', label='Stability Threshold (0.50)')
    
    ax.set_xlabel("Time step")
    ax.set_ylabel("Systemic Tau $\\tau_s$")
    ax.set_title("Systemic Tau Evolution")
    ax.legend(loc="upper left")
    
    return ax

def plot_joint_episodes(episodes, M_series, A_series, ax=None):
    """
    Plots the Critical Mass (M) and Anti-synchronization (A) series and highlights joint episodes.
    """
    plt = _check_matplotlib()
    
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 4))
        
    t = np.arange(len(M_series))
    ax.plot(t, M_series, color='purple', label='Critical Mass (M)', alpha=0.7)
    
    ax2 = ax.twinx()
    ax2.plot(t, A_series, color='orange', label='Anti-sync (A)', alpha=0.7)
    
    # Highlight joint episodes if provided
    if episodes is not None:
        for ep in episodes:
            ax.axvspan(ep['start'], ep['end'], color='yellow', alpha=0.3)
            
    ax.set_xlabel("Time step")
    ax.set_ylabel("Critical Mass $M$")
    ax2.set_ylabel("Anti-sync $A$")
    ax.set_title("Layer 2: Relational Coherence & Joint Episodes")
    
    # Combine legends from both axes
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, loc="upper right")
    
    return ax

def plot_ontological_layers(hp_z, lam, tt, M_series, A_series, t_star=None):
    """
    Plots a multi-panel figure showing the progression of the three ontological layers.
    """
    plt = _check_matplotlib()
    
    fig, axs = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    t = np.arange(len(hp_z))
    
    # Layer 1: Local Intensification
    axs[0].plot(t, hp_z, label='Hyper-persistence (Z)', color='blue')
    axs[0].plot(t, lam, label='Laminarity (LAM)', color='cyan')
    axs[0].plot(t, tt, label='Trapping Time (TT)', color='teal')
    axs[0].set_ylabel("Layer 1 Metrics")
    axs[0].legend(loc="upper right")
    axs[0].set_title("Layer 1: Local Intensification")
    
    # Layer 2: Relational Coherence
    axs[1].plot(t, M_series, color='purple', label='Critical Mass (M)')
    axs[1].plot(t, A_series, color='orange', label='Anti-sync (A)')
    axs[1].set_ylabel("Layer 2 Metrics")
    axs[1].legend(loc="upper right")
    axs[1].set_title("Layer 2: Relational Coherence")
    
    # Layer 3: Ontological Ascent
    # Display the transition point
    axs[2].text(0.5, 0.5, 'Ontological Ascent Detection', 
                horizontalalignment='center', verticalalignment='center', transform=axs[2].transAxes)
    if t_star is not None:
        for ax in axs:
            ax.axvline(x=t_star, color='red', linestyle='-', linewidth=2, label='Transition $t^*$')
        axs[2].text(0.5, 0.3, f'Transition confirmed at $t^* = {t_star}$', 
                    horizontalalignment='center', verticalalignment='center', transform=axs[2].transAxes, color='red', fontsize=12)
        axs[0].legend()
    
    axs[2].set_xlabel("Time step")
    axs[2].set_yticks([])
    axs[2].set_title("Layer 3: Ontological Ascent")
    
    plt.tight_layout()
    return fig
