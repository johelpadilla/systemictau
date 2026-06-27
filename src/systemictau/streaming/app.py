try:
    import faust
except ImportError:
    pass

import os
import json
import numpy as np
from systemictau import systemic_tau

# Ensure this runs gracefully if faust is missing (e.g. standard install)
if 'faust' in globals():
    kafka_broker = os.getenv("KAFKA_BROKER_URL", "kafka://localhost:9092")
    
    app = faust.App(
        'systemictau-stream-processor',
        broker=kafka_broker,
        value_serializer='json',
        store='rocksdb://', # Enables durable local state recovery
        topic_partitions=4, # Horizontal scaling
    )
    
    # Kafka Topic definitions
    raw_data_topic = app.topic('sys.raw_data', partitions=4)
    transitions_topic = app.topic('sys.transitions', partitions=4)
    
    # Stateful table to keep a rolling window
    window_state = app.Table('sliding_windows', default=list)
    
    @app.agent(raw_data_topic)
    async def process_stream(stream):
        async for payload in stream:
            tenant_id = payload.get("tenant_id", "default")
            new_data_point = payload.get("vector")  # e.g., [1.2, 3.4, ...]
            
            # Append to rolling window (simplified logic)
            window = window_state[tenant_id]
            window.append(new_data_point)
            
            # Maintain fixed window size (e.g., 13)
            if len(window) > 13:
                window.pop(0)
            
            window_state[tenant_id] = window
            
            # Compute Systemic Tau if we have enough data
            if len(window) == 13:
                X = np.array(window)
                # Compute Tau
                res = systemic_tau(X, window_size=13, engine="numba")
                latest_tau = res.taus_global[-1]
                
                # Check anomaly threshold for Critical Mass (e.g. > 0.8)
                if latest_tau > 0.8:
                    await transitions_topic.send(value={
                        "tenant_id": tenant_id,
                        "tau": float(latest_tau),
                        "message": "Potential Critical Mass Detected"
                    })
