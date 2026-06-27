from google import genai
from systemictau.config import settings

def run_discovery_engine_sync(context: str, tau_val: float, update_callback=None):
    """
    The True Systemic Tau Epistemic Engine (Standalone Version).
    Orchestrates the Ontologist, Advocate, Critic, and Judge agents.
    
    Args:
        context (str): The domain and context string (e.g. data column anomalies).
        tau_val (float): The mathematical structural break magnitude.
        update_callback (callable): Optional callback function that takes a string 
                                    to stream updates to the GUI.
    """
    
    def log(msg):
        if update_callback:
            update_callback(msg)
        else:
            print(msg)

    # Validate API Key
    api_key = settings.google_api_key
    if not api_key or api_key == "DUMMY_GEMINI_KEY":
        raise ValueError("API key not valid. Please pass a valid API key.")
        
    client = genai.Client(api_key=api_key)
    model_id = 'gemini-2.5-flash'
    
    # ---------------------------------------------------------
    # AGENT 1: The Ontologist (Hypothesizer)
    # ---------------------------------------------------------
    log("\\n[Agent 1: Ontologist] Formulating initial hypothesis based on Tau transition...\\n")
    ontologist_prompt = (
        f"Context: {context}\\n"
        f"Mathematical Transition (Tau): {tau_val}\\n\\n"
        "As an expert Systems Ontologist, formulate a strict, 1-sentence causal scientific hypothesis "
        "explaining this structural anomaly. Focus on systemic collapse geometry."
    )
    try:
        response_ont = client.models.generate_content(model=model_id, contents=ontologist_prompt)
        hypothesis = response_ont.text.strip()
        log(f"      -> Hypothesis: {hypothesis}\\n")
    except Exception as e:
        raise RuntimeError(f"Ontologist Agent Error: {e}")

    # ---------------------------------------------------------
    # AGENT 2: The Experimentalist (Mocked Data Retrieval)
    # ---------------------------------------------------------
    log("\\n[Agent 2: Experimentalist] Fetching empirical evidence...\\n")
    # Simulating the PubMedSearchTool output for the desktop app so it doesn't hang on network scraping
    evidence_summary = (
        "Empirical literature search simulated. Patterns of rapid variance growth "
        "strongly correlate with phase transitions and systemic bifurcation points."
    )
    log(f"      -> Evidence: {evidence_summary}\\n")

    # ---------------------------------------------------------
    # AGENT 3A: The Advocate (Defense)
    # ---------------------------------------------------------
    log("\\n[Agent 3A: Advocate] Defending the hypothesis...\\n")
    advocate_prompt = (
        f"Hypothesis: {hypothesis}\\n"
        f"Evidence: {evidence_summary}\\n\\n"
        "As the Advocate, argue aggressively in 2-3 sentences why this evidence "
        "definitively PROVES the hypothesis is an absolute systemic truth."
    )
    try:
        adv_response = client.models.generate_content(model=model_id, contents=advocate_prompt)
        advocate_arg = adv_response.text.strip()
        log(f"      -> Defense: {advocate_arg}\\n")
    except Exception as e:
        raise RuntimeError(f"Advocate Agent Error: {e}")

    # ---------------------------------------------------------
    # AGENT 3B: The Critic (Attack)
    # ---------------------------------------------------------
    log("\\n[Agent 3B: Critic] Attacking the hypothesis...\\n")
    critic_prompt = (
        f"Hypothesis: {hypothesis}\\n"
        f"Evidence: {evidence_summary}\\n\\n"
        "As the Critic, argue aggressively in 2-3 sentences why this evidence "
        "is INSUFFICIENT, FLAWED, or purely circumstantial."
    )
    try:
        crit_response = client.models.generate_content(model=model_id, contents=critic_prompt)
        critic_arg = crit_response.text.strip()
        log(f"      -> Attack: {critic_arg}\\n")
    except Exception as e:
        raise RuntimeError(f"Critic Agent Error: {e}")

    # ---------------------------------------------------------
    # AGENT 4: The Judge (Verdict)
    # ---------------------------------------------------------
    log("\\n[Agent 4: Judge] Weighing arguments and issuing verdict...\\n")
    judge_prompt = (
        f"Advocate argues: {advocate_arg}\\n"
        f"Critic argues: {critic_arg}\\n\\n"
        "Based on this debate, what is the final objective confidence score for the hypothesis? "
        "Reply ONLY with a float between 0.0 and 1.0. No other text."
    )
    try:
        judge_response = client.models.generate_content(model=model_id, contents=judge_prompt)
        try:
            confidence = float(judge_response.text.strip())
        except ValueError:
            confidence = 0.50
        log(f"      -> Final Confidence Score (p*): {confidence}\\n")
    except Exception as e:
        confidence = 0.50
        log(f"      -> Judge Agent Error: {e}. Defaulting to {confidence}\\n")

    return hypothesis, confidence
