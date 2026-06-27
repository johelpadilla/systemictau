import os
try:
    from neo4j import GraphDatabase
except ImportError:
    pass

class KnowledgeGraphService:
    def __init__(self, uri=None, user=None, password=None):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        
        # Only initialize if neo4j is available
        if 'GraphDatabase' in globals():
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        else:
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def persist_ontological_ascent(self, tenant_id: str, t_star: int, tau_value: float, description: str):
        """
        Creates a (System)-[:UNDERWENT]->(Ascent) relationship in the Neo4j Knowledge Graph.
        Allows for traversing causality chains of ontological transitions.
        """
        if not self.driver:
            print("Neo4j driver not initialized. Skipping graph persistence.")
            return
            
        query = """
        MERGE (s:System {tenant_id: $tenant_id})
        CREATE (a:OntologicalAscent {
            t_star: $t_star, 
            tau: $tau_value, 
            description: $description,
            timestamp: timestamp()
        })
        CREATE (s)-[:UNDERWENT]->(a)
        RETURN id(a) as node_id
        """
        with self.driver.session() as session:
            result = session.run(query, tenant_id=tenant_id, t_star=t_star, tau_value=tau_value, description=description)
            return result.single()["node_id"]
            
    def get_historical_context(self, tenant_id: str, limit: int = 5) -> list:
        """
        Retrieves the last N transitions for a specific tenant to provide Graph-RAG context.
        """
        if not self.driver:
            return []
            
        query = """
        MATCH (s:System {tenant_id: $tenant_id})-[:UNDERWENT]->(a:OntologicalAscent)
        RETURN a.t_star AS t_star, a.tau AS tau, a.description AS description, a.timestamp AS timestamp
        ORDER BY a.timestamp DESC
        LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(query, tenant_id=tenant_id, limit=limit)
            return [record.data() for record in result]
            
    def persist_agent_report(self, ascent_node_id: int, report_text: str):
        """
        Attaches an LLM generated ReportNode to an AscentNode in the Graph.
        """
        if not self.driver:
            return
            
        query = """
        MATCH (a:OntologicalAscent) WHERE id(a) = $node_id
        CREATE (r:ReportNode {
            content: $content,
            timestamp: timestamp()
        })
        CREATE (a)-[:SYNTHESIZED_INTO]->(r)
        """
        with self.driver.session() as session:
            session.run(query, node_id=ascent_node_id, content=report_text)
