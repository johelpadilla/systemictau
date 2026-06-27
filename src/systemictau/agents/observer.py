try:
    import faust
except ImportError:
    pass

import os
from tenacity import retry, stop_after_attempt, wait_exponential
from systemictau.platform.ai import generate_latex_report
from systemictau.graph.db import KnowledgeGraphService
from systemictau.config import settings

if 'faust' in globals():
    kafka_broker = settings.kafka_broker
    
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
            
            # 2. Query Neo4j for Historical Context (Graph-RAG)
            history = kg.get_historical_context(tenant_id=tenant_id)
            context_str = "\\n".join([f"- At t*={h['t_star']}, tau={h['tau']}: {h['description']}" for h in history])
            
            # 3. Generate Hypothesis Report via LLM with context
            @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
            def robust_generate_report(topic):
                return generate_latex_report(episodes=[1], t_star=0, topic=topic)

            try:
                topic = f"Tenant {tenant_id} stream. Historical context:\\n{context_str}"
                report = robust_generate_report(topic)
                print("[AGENT OBSERVER] Autonomously generated LaTeX Report with Graph-RAG.")
                
                # 4. Persist Report to Graph
                kg.persist_agent_report(node_id, report)
                print(f"[AGENT OBSERVER] Persisted report to Neo4j linked to Ascent {node_id}")
            except Exception as e:
                print(f"[AGENT OBSERVER] LLM Generation Failed after 3 retries: {e}")
                kg.persist_agent_report(node_id, "Report Generation Failed. Defaulting to Heuristic Fallback.")
