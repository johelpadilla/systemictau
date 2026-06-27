try:
    import faust
except ImportError:
    pass

import os
from systemictau.platform.ai import generate_latex_report
from systemictau.graph.db import KnowledgeGraphService

if 'faust' in globals():
    kafka_broker = os.getenv("KAFKA_BROKER_URL", "kafka://localhost:9092")
    
    app = faust.App(
        'systemictau-agent-observer',
        broker=kafka_broker,
        value_serializer='json',
    )
    
    transitions_topic = app.topic('sys.transitions')
    
    # Initialize Neo4j Service
    kg = KnowledgeGraphService()
    
    @app.agent(transitions_topic)
    async def observe_transitions(stream):
        """
        Autonomous LLM Agent that observes the Kafka transition topic, 
        persists to the Knowledge Graph, and generates analytical reports.
        """
        async for transition in stream:
            tenant_id = transition.get("tenant_id")
            tau_val = transition.get("tau")
            msg = transition.get("message")
            
            print(f"[AGENT OBSERVER] Detected anomaly for {tenant_id}: {msg} (Tau={tau_val})")
            
            # 1. Persist to Knowledge Graph
            node_id = kg.persist_ontological_ascent(
                tenant_id=tenant_id, 
                t_star=0, # placeholder for true t* calculation 
                tau_value=tau_val, 
                description=msg
            )
            print(f"[AGENT OBSERVER] Persisted to Neo4j Graph. Node ID: {node_id}")
            
            # 2. Generate Hypothesis Report via LLM
            # (In production, this would query Neo4j for historical context before prompting the LLM)
            try:
                report = generate_latex_report(episodes=[1], t_star=0, topic=f"Tenant {tenant_id} stream")
                print("[AGENT OBSERVER] Autonomously generated LaTeX Report:")
                print(report)
            except Exception as e:
                print(f"[AGENT OBSERVER] LLM Generation Failed: {e}")
