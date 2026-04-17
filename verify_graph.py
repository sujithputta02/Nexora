"""
Verify graph population
"""

from backend.graph_store import GraphStore

print("="*80)
print("GRAPH VERIFICATION")
print("="*80)

graph = GraphStore()

# Count nodes by type
print("\n[1] Node Count by Type:")

node_types = [
    "Mission", "LaunchVehicle", "Stage", "Engine", "Payload",
    "Organization", "Country", "ResearchArea", "Technology"
]

total_nodes = 0

for node_type in node_types:
    try:
        result = graph.driver.execute_query(f"MATCH (n:{node_type}) RETURN COUNT(n) as count")
        count = result.records[0]["count"] if result.records else 0
        total_nodes += count
        print(f"  {node_type}: {count}")
    except Exception as e:
        print(f"  {node_type}: Error - {e}")

print(f"\n  Total Nodes: {total_nodes}")

# Sample some nodes
print("\n[2] Sample Nodes:")

try:
    result = graph.driver.execute_query("MATCH (n) RETURN n.name as name, labels(n)[0] as type LIMIT 20")
    for record in result.records:
        print(f"  - {record['name']} ({record['type']})")
except Exception as e:
    print(f"  Error: {e}")

graph.close()

print("\n" + "="*80)
print("✅ Graph verification complete!")
print("="*80)
