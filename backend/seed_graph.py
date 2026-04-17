from backend.graph_store import GraphStore

def seed():
    graph = GraphStore()
    graph.setup_schema()
    
    print("Seeding Knowledge Graph with Mission Data...")
    
    # 1. Missions
    graph.add_entity("Mission", {"name": "GSLV Mk III", "stages": 3, "status": "active"})
    graph.add_entity("Mission", {"name": "Chandrayaan-1", "objective": "Lunar orbit", "director": "M. Annadurai"})
    graph.add_entity("Mission", {"name": "Chandrayaan-2", "objective": "Lunar orbiter/lander", "director": "M. Vanitha"})
    graph.add_entity("Mission", {"name": "Chandrayaan-3", "objective": "Lunar landing", "director": "P. Veeramuthuvel", "rover": "Pragyan"})
    graph.add_entity("Mission", {"name": "GSAT-11", "type": "Communication", "mass": "5854 kg"})
    graph.add_entity("Mission", {"name": "GSAT-19", "type": "Communication", "mass": "3136 kg"})
    graph.add_entity("Mission", {"name": "EOS-03", "type": "Earth Observation", "status": "failed"})
    
    # 2. People & Roles
    graph.add_entity("Person", {"name": "M. Vanitha", "role": "Project Director"})
    graph.add_entity("Person", {"name": "Ritu Karidhal", "role": "Mission Director"})
    graph.add_entity("Person", {"name": "P. Veeramuthuvel", "role": "Project Director"})
    graph.add_entity("Person", {"name": "M. Annadurai", "role": "Project Director"})
    
    # 3. Launch Vehicles
    graph.add_entity("LaunchVehicle", {"name": "PSLV", "payload_to_leo": "3800 kg"})
    graph.add_entity("LaunchVehicle", {"name": "GSLV Mk III", "payload_to_leo": "10000 kg"})
    
    # 4. Engines
    graph.add_entity("Engine", {"name": "CE-20", "type": "Cryogenic"})
    graph.add_entity("Engine", {"name": "S200", "type": "Solid"})
    graph.add_entity("Engine", {"name": "Vikas", "type": "Liquid"})
    
    # 5. Relationships
    graph.add_relationship("Mission", "Chandrayaan-1", "Person", "M. Annadurai", "LED_BY")
    graph.add_relationship("Mission", "Chandrayaan-2", "Person", "M. Vanitha", "LED_BY")
    graph.add_relationship("Mission", "Chandrayaan-2", "Person", "Ritu Karidhal", "MANAGED_BY")
    graph.add_relationship("Mission", "Chandrayaan-3", "Person", "P. Veeramuthuvel", "LED_BY")
    graph.add_relationship("Mission", "GSLV Mk III", "Engine", "CE-20", "USES")
    graph.add_relationship("Mission", "GSLV Mk III", "Engine", "S200", "USES")
    graph.add_relationship("Mission", "GSAT-11", "Mission", "GSLV Mk III", "LAUNCHED_BY")
    graph.add_relationship("Mission", "GSAT-19", "Mission", "GSLV Mk III", "LAUNCHED_BY")
    graph.add_relationship("Mission", "Chandrayaan-3", "Mission", "GSLV Mk III", "LAUNCHED_BY")
    
    print("Graph Seeding Complete.")
    graph.close()

if __name__ == "__main__":
    seed()
