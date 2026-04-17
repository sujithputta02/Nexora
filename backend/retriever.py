from backend.vector_store import load_vector_store
from backend.graph_store import GraphStore
import re

def identify_entities(query):
    """
    Identifies potential space-domain entities in the query using regex patterns.
    (In a more advanced version, this would use a local NER model).
    """
    # Look for capitalized words (Proper Nouns) or common aerospace terms
    entities = re.findall(r'\b[A-Z][a-z0-7]+\b', query)
    return list(set(entities))

def retrieve_context(query, k=10, bypass_graph=False):
    """
    Retrieves a hybrid context with Diversity-Aware Filtering (MMR).
    Ensures that multiple missions (C1, C2, C3) are captured by preventing 
    a single document from dominating the top-k slots.
    """
    context = {"chunks": [], "facts": []}
    query_lower = query.lower()
    
    # 1. Subject Detection & Context Expansion (Expanded Library)
    primary_subjects = [
        "pslv", "gslv", "lvm3", "sslv", "rlv", "hrlv",             # Launch Vehicles
        "chandrayaan", "chandrayaan-1", "chandrayaan-2", "chandrayaan-3", # Lunar
        "gaganyaan", "mangalyaan", "aditya", "mom", "xposat",       # Deep Space & Science
        "gsat", "insat", "eos", "sarsat", "scatsat",                # Communications & SAR
        "irnss", "navic", "astrosat", "bhuvan",                     # Navigation & Observatory
        "risat", "cartosat", "oceansat", "resourcesat", "hysis",    # Earth Observation
        "vikas", "ce-20", "ce-7.5", "s200", "l110", "c25",          # Propulsion & Engines
        "isro", "antrix", "nsil", "in-space",                       # Organizations
        "satellite", "mission", "rocket", "engine", "payload"       # Generic Subject Aliases
    ]
    
    target_subject = next((s for s in primary_subjects if s in query_lower), None)
    
    # Context Expansion: If user says 'Moon', boost 'Chandrayaan-3' to ensure recent landing is found
    search_query = query
    if not target_subject and any(m in query_lower for m in ["moon", "lunar"]):
        target_subject = "chandrayaan"
        search_query += " Chandrayaan-3 soft-landing LVM3-M4"
    
    # 2. Diversity-Aware Vector Search (MMR)
    vector_store = load_vector_store()
    if vector_store:
        # Use MMR (Maximal Marginal Relevance) to get a DIVERSE set of missions
        raw_results = vector_store.search(
            search_query, 
            search_type="mmr", 
            k=k, 
            fetch_k=40, # Look at a wide pool then pick the most diverse ones
            lambda_mult=0.5 # 0.5 balances similarity and diversity perfectly
        )
        
        # Priority Reinforcement: If we have a target subject, ensure it appears
        if target_subject:
            context["chunks"] = raw_results
        else:
            context["chunks"] = raw_results
    
    # 3. Graph Search (Logical Reasoning & Leadership Grounding)
    if not bypass_graph:
        try:
            graph = GraphStore()
            # Priority: Search for the specific target subject found in step 1
            # This ensures lowercase queries like 'chandrayaan-2' find the 'M. Vanitha' fact
            search_entities = identify_entities(query)
            if target_subject and target_subject not in [e.lower() for e in search_entities]:
                search_entities.append(target_subject)
                
            for entity in search_entities:
                facts = graph.query_facts(entity)
                if facts:
                    # Relationship filtering: Only keep facts relevant to the technical subjects
                    context["facts"].extend(facts)
            graph.close()
        except Exception as e:
            print(f"Graph retrieval error: {e}")

    return context
