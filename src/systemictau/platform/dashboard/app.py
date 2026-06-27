import streamlit as st
import pandas as pd
import numpy as np

from systemictau import systemic_tau, from_dataframe, ChaosGenerator
from systemictau.visualization import plot_tau_evolution

st.set_page_config(page_title="Systemic Tau Platform", page_icon="📈", layout="wide")

st.title("Systemic Tau Dashboard v3.0")
st.markdown("Analyze multivariate complex systems and detect *Ontological Ascent*.")

tab1, tab2, tab3 = st.tabs(["Data Upload & Chaos", "Systemic Tau Computation", "Layer Analysis"])

with tab1:
    st.header("Data Input")
    input_mode = st.radio("Select input mode:", ["Synthetic (Chaos Generator)", "Upload CSV"])
    
    df = None
    if input_mode == "Synthetic (Chaos Generator)":
        n_steps = st.slider("Time steps (T)", 100, 2000, 500)
        n_comp = st.slider("Number of components (N)", 2, 20, 5)
        coupling = st.slider("Coupling Strength", 0.0, 0.5, 0.1)
        
        if st.button("Generate Data"):
            X = ChaosGenerator.logistic_map_coupled(n_steps, n_comp, coupling=coupling)
            df = pd.DataFrame(X, columns=[f"V{i+1}" for i in range(n_comp)])
            st.session_state['df'] = df
            st.success("Synthetic data generated!")
            
    else:
        uploaded_file = st.file_uploader("Upload CSV", type="csv")
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.session_state['df'] = df
            st.success("File uploaded!")
            
    if 'df' in st.session_state:
        st.write("Preview:")
        st.dataframe(st.session_state['df'].head())

with tab2:
    st.header("Systemic Tau ($\\tau_s$)")
    
    if 'df' in st.session_state:
        window_size = st.slider("Sliding Window Size", 3, 100, 13)
        
        if st.button("Compute Systemic Tau"):
            with st.spinner("Computing..."):
                res = from_dataframe(st.session_state['df'], window_size=window_size)
                st.session_state['res'] = res
                
            st.success(f"Computed in {res.metadata['computation_time_seconds']:.2f} seconds.")
            
            st.subheader("Evolution Plot")
            fig = plot_tau_evolution(res.taus_global).figure
            st.pyplot(fig)
    else:
        st.info("Please load data in the first tab.")

with tab3:
    st.header("Ontological Layers & Joint Episodes")
    st.markdown("*Coming soon in future v3.0 updates.*")
    
    if 'res' in st.session_state:
        st.metric(label="Global Mean $\\tau_s$", value=f"{np.nanmean(st.session_state['res'].taus_global):.3f}")
