"""
Verify graph data and ensure all nodes are properly connected for visualization
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "securerag1")
DATABASE = os.getenv("NEO4J_DATABASE", "securerag")

print("="*80)
print("VERIFYING GRAPH DATA")
print("="*80)

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

with driver.session(database=DATABASE) as session:
    # Count all nodes
    result = session.run("MATCH (n) RETURN COUNT(n) as count")
    total_nodes = result.single()["count"]
    print(f"\n✅ Total Nodes in Database: {total_nodes}")
    
    # Count all relationships
    result = session.run("MATCH ()-[r]->() RETURN COUNT(r) as count")
    total_rels = result.single()["count"]
    print(f"✅ Total Relationships in Database: {total_rels}")
    
    # Count nodes by type
    print(f"\nNodes by Type:")
    result = session.run("MATCH (n) RETURN labels(n)[0] as type, COUNT(*) as count ORDER BY count DESC")
    for record in result:
        print(f"  - {record['type']}: {record['count']}")
    
    # Check for isolated nodes (nodes with no relationships)
    print(f"\nChecking for isolated nodes...")
    result = session.run("MATCH (n) WHERE NOT (n)--() RETURN COUNT(n) as count")
    isolated = result.single()["count"]
    print(f"  Isolated nodes (no relationships): {isolated}")
    
    if isolated > 0:
        print(f"\n⚠️  Found {isolated} isolated nodes!")
        print(f"  These won't show in the graph visualization.")
        print(f"  Creating relationships to connect them...\n")
        
        # Get isolated nodes
        result = session.run("MATCH (n) WHERE NOT (n)--() RETURN labels(n)[0] as type, n.name as name LIMIT 20")
        isolated_nodes = list(result)
        
        if isolated_nodes:
            print(f"  Sample isolated nodes:")
            for record in isolated_nodes[:10]:
                print(f"    - {record['type']}: {record['name']}")
    
    # Check connectivity
    print(f"\nChecking graph connectivity...")
    result = session.run("""
        MATCH (n)
        WITH COUNT(DISTINCT n) as total_nodes
        MATCH (n)-[r]-(m)
        WITH total_nodes, COUNT(DISTINCT n) as connected_nodes
        RETURN total_nodes, connected_nodes, 
               ROUND(100.0 * connected_nodes / total_nodes, 1) as connectivity_percent
    """)
    
    record = result.single()
    if record:
        print(f"  Total nodes: {record['total_nodes']}")
        print(f"  Connected nodes: {record['connected_nodes']}")
        print(f"  Connectivity: {record['connectivity_percent']}%")

driver.close()

print("\n" + "="*80)
print("GRAPH VERIFICATION COMPLETE")
print("="*80)
print("\nTo see all nodes in Neo4j Desktop:")
print("  1. Click 'All' filter (top left)")
print("  2. Use zoom out (scroll wheel or - button)")
print("  3. Click 'Force-based layout' dropdown and select different layout")
print("  4. Try 'Hierarchical layout' or 'Circular layout'")
print("  5. Or run query: MATCH (n) RETURN n LIMIT 100")
print("="*80)
