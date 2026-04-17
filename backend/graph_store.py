import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
DATABASE = os.getenv("NEO4J_DATABASE", "neo4j") # Default to neo4j if not set

class GraphStore:
    def __init__(self):
        self.driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

    def close(self):
        self.driver.close()

    def _get_session(self):
        return self.driver.session(database=DATABASE)

    def verify_connectivity(self):
        """
        Verifies if the Neo4j database is reachable.
        """
        try:
            with self._get_session() as session:
                session.run("RETURN 1")
            return True
        except Exception as e:
            print(f"Neo4j connectivity check failed: {e}")
            return False

    def setup_schema(self):
        """
        Sets up the initial schema constraints for the Knowledge Graph.
        """
        with self._get_session() as session:
            # Create constraints to ensure uniqueness using correct Neo4j 5.x syntax
            # Syntax: CREATE CONSTRAINT [name] IF NOT EXISTS FOR (n:Label) REQUIRE n.prop IS UNIQUE
            
            try:
                session.run("CREATE CONSTRAINT mission_name IF NOT EXISTS FOR (m:Mission) REQUIRE m.name IS UNIQUE")
                session.run("CREATE CONSTRAINT lv_name IF NOT EXISTS FOR (lv:LaunchVehicle) REQUIRE lv.name IS UNIQUE")
                session.run("CREATE CONSTRAINT stage_name IF NOT EXISTS FOR (s:Stage) REQUIRE s.name IS UNIQUE")
                session.run("CREATE CONSTRAINT engine_name IF NOT EXISTS FOR (e:Engine) REQUIRE e.name IS UNIQUE")
                session.run("CREATE CONSTRAINT payload_name IF NOT EXISTS FOR (p:Payload) REQUIRE p.name IS UNIQUE")
                session.run("CREATE CONSTRAINT org_name IF NOT EXISTS FOR (o:Organization) REQUIRE o.name IS UNIQUE")
                session.run("CREATE CONSTRAINT country_name IF NOT EXISTS FOR (c:Country) REQUIRE c.name IS UNIQUE")
                session.run("CREATE CONSTRAINT research_area_name IF NOT EXISTS FOR (r:ResearchArea) REQUIRE r.name IS UNIQUE")
                session.run("CREATE CONSTRAINT technology_name IF NOT EXISTS FOR (t:Technology) REQUIRE t.name IS UNIQUE")
                session.run("CREATE CONSTRAINT partnership_name IF NOT EXISTS FOR (p:Partnership) REQUIRE p.name IS UNIQUE")
                session.run("CREATE CONSTRAINT publication_name IF NOT EXISTS FOR (p:Publication) REQUIRE p.name IS UNIQUE")
                session.run("CREATE CONSTRAINT patent_name IF NOT EXISTS FOR (p:Patent) REQUIRE p.name IS UNIQUE")
            except Exception as e:
                print(f"Schema setup warning (might be older Neo4j version): {e}")

    def add_entity(self, label, properties):
        """
        Adds a node to the graph with the given label and properties.
        """
        def _add_entity_tx(tx, label, name, props):
            query = f"MERGE (n:{label} {{name: $name}}) SET n += $props"
            tx.run(query, name=name, props=props)
            
        with self._get_session() as session:
            session.execute_write(_add_entity_tx, label, properties.get("name"), properties)

    def add_relationship(self, start_label, start_name, end_label, end_name, relationship_type):
        """
        Adds a relationship between two nodes.
        """
        def _add_rel_tx(tx, start_label, start_name, end_label, end_name, relationship_type):
            query = f"""
            MATCH (a:{start_label} {{name: $start_name}})
            MATCH (b:{end_label} {{name: $end_name}})
            MERGE (a)-[:{relationship_type}]->(b)
            """
            try:
                tx.run(query, start_name=start_name, end_name=end_name)
            except Exception as e:
                # Silently handle relationship creation errors (nodes might not exist)
                pass
            
        with self._get_session() as session:
            try:
                session.execute_write(_add_rel_tx, start_label, start_name, end_label, end_name, relationship_type)
            except Exception as e:
                # Connection errors will be retried by Neo4j driver
                pass
    
    def count_nodes(self):
        """
        Returns the total number of nodes in the database.
        """
        with self._get_session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            return result.single()["count"]
    
    def query_facts(self, entity_name):
        """
        Retrieves all facts related to a specific entity (up to 2 hops).
        """
        query = """
        MATCH (n) WHERE n.name =~ '(?i)' + $name
        MATCH (n)-[r1]-(m)
        OPTIONAL MATCH (m)-[r2]-(p)
        WHERE p <> n
        RETURN 
            type(r1) as relationship, 
            labels(m) as target_label, 
            m.name as target_name,
            type(r2) as second_hop_rel,
            labels(p) as second_hop_label,
            p.name as second_hop_name
        """
        with self._get_session() as session:
            result = session.run(query, name=entity_name)
            return [record.data() for record in result]

    def get_all_entity_names(self):
        """
        Retrieves all node names from the graph to build the dynamic gazetteer.
        """
        query = "MATCH (n) WHERE n.name IS NOT NULL RETURN DISTINCT n.name as name"
        with self._get_session() as session:
            result = session.run(query)
            return [record["name"] for record in result]

if __name__ == "__main__":
    # Test connection
    try:
        graph = GraphStore()
        graph.setup_schema()
        print("Connected to Neo4j and schema setup complete.")
        graph.close()
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")
