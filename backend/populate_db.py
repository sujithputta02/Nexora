from backend.ingestion import load_documents, split_documents
from backend.vector_store import create_vector_store
from backend.graph_store import GraphStore
import re
import os
import json
from langchain_ollama import ChatOllama

class LLMEntityExtractor:
    def __init__(self, model="llama3"):
        self.llm = ChatOllama(
            model=model,
            temperature=0.0,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )

    def extract(self, text):
        """
        Zero-shot LLM-based entity extraction for domain adaptation.
        """
        prompt = (
            "You are a Domain Intelligence Specialist. Extract core technical components from the text.\n"
            "Categories: Mission, LaunchVehicle, Stage, Engine, Payload, Organization, Country, ResearchArea, Technology, Partnership, Publication, Patent.\n"
            "Return ONLY valid JSON: `{\"Mission\": [], \"LaunchVehicle\": [], \"Stage\": [], \"Engine\": [], \"Payload\": [], \"Organization\": [], \"Country\": [], \"ResearchArea\": [], \"Technology\": [], \"Partnership\": [], \"Publication\": [], \"Patent\": []}`.\n\n"
            f"TEXT:\n{text[:2000]}\n\n"
            "JSON:"
        )
        try:
            response = self.llm.invoke(prompt)
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "{" in content:
                content = content[content.find("{"):content.rfind("}")+1]
            
            data = json.loads(content)
            return {k: set(v) for k, v in data.items() if isinstance(v, list)}
        except Exception as e:
            print(f"LLM Extraction Warning: {e}")
            return {k: set() for k in ["Mission", "LaunchVehicle", "Stage", "Engine", "Payload", "Organization", "Country", "ResearchArea", "Technology", "Partnership", "Publication", "Patent"]}

# Comprehensive heuristic entity extraction (Offline/Rule-based)
def extract_entities(text):
    """
    Extracts comprehensive entities from ISRO documents including:
    Missions, Launch Vehicles, Stages, Engines, Payloads, Organizations, Countries,
    Research Areas, Technologies, Partnerships, Publications, Patents
    """
    entities = {
        "Mission": set(),
        "LaunchVehicle": set(),
        "Stage": set(),
        "Engine": set(),
        "Payload": set(),
        "Organization": set(),
        "Country": set(),
        "ResearchArea": set(),
        "Technology": set(),
        "Partnership": set(),
        "Publication": set(),
        "Patent": set()
    }
    
    # Launch Vehicles - PSLV, GSLV, LVM3, SSLV variants
    lv_matches = re.findall(r"\b(PSLV|GSLV|LVM3|SSLV)[-\s]?([A-Za-z0-9]*)\b", text)
    for match in lv_matches:
        lv_name = f"{match[0]}{'-' + match[1] if match[1] else ''}".strip()
        entities["LaunchVehicle"].add(lv_name)
    
    # Stages - First, Second, Third, Fourth stages
    stage_matches = re.findall(r"\b(Stage\s*\d+|First\s*Stage|Second\s*Stage|Third\s*Stage|Fourth\s*Stage|L40|L110|GS1|GS2|GS3|GS4)\b", text, re.IGNORECASE)
    entities["Stage"].update(stage_matches)
    
    # Engines - Vikas, Cryogenic, CE-20, CE-7.5, S200, F10, F11, etc.
    engine_matches = re.findall(r"\b(Vikas|Cryogenic|CE-20|CE-7\.5|S200|F10|F11|F12|F13|F14|F15|F16|F17|F18|F19|F20|Solid\s*Rocket\s*Booster|SRB)\b", text, re.IGNORECASE)
    entities["Engine"].update(engine_matches)
    
    # Missions - All ISRO missions including recent ones
    mission_patterns = [
        r"\b(Chandrayaan-[0-3])\b",  # Chandrayaan-1, 2, 3
        r"\b(Mangalyaan|Mars\s*Orbiter\s*Mission|MOM)\b",
        r"\b(Aditya[-\s]?L1)\b",
        r"\b(Gaganyaan)\b",
        r"\b(EOS-\d+)\b",
        r"\b(GSAT-\d+[A-Z]?)\b",
        r"\b(IRNSS|NavIC)\b",
        r"\b(AstroSat)\b",
        r"\b(RISAT-[0-9A-Z]+)\b",
        r"\b(Cartosat-[0-9]+)\b",
        r"\b(Resourcesat-[0-9]+)\b",
        r"\b(Oceansat-[0-9]+)\b",
        r"\b(Megha[-\s]?Tropiques)\b",
        r"\b(SARAL)\b",
        r"\b(Scatsat-[0-9]+)\b",
        r"\b(INSAT-[0-9A-Z]+)\b"
    ]
    for pattern in mission_patterns:
        mission_matches = re.findall(pattern, text, re.IGNORECASE)
        entities["Mission"].update(mission_matches)
    
    # Payloads - Satellites, instruments, sensors
    payload_patterns = [
        r"\b(Terrain\s*Mapping\s*Camera|TMC)\b",
        r"\b(Hyper\s*Spectral\s*Imager|HySI)\b",
        r"\b(Lunar\s*Reconnaissance\s*Orbiter|LRO)\b",
        r"\b(Synthetic\s*Aperture\s*Radar|SAR)\b",
        r"\b(Visible\s*Light\s*Imager|VLI)\b",
        r"\b(Infrared\s*Imager|IRI)\b",
        r"\b(Lander|Rover|Orbiter)\b",
        r"\b(Instrument\s*Cluster|IC)\b"
    ]
    for pattern in payload_patterns:
        payload_matches = re.findall(pattern, text, re.IGNORECASE)
        entities["Payload"].update(payload_matches)
    
    # Organizations - ISRO, DRDO, HAL, etc.
    org_patterns = [
        r"\b(ISRO|Indian\s*Space\s*Research\s*Organisation)\b",
        r"\b(DRDO|Defence\s*Research\s*and\s*Development\s*Organisation)\b",
        r"\b(HAL|Hindustan\s*Aeronautics\s*Limited)\b",
        r"\b(LPSC|Liquid\s*Propulsion\s*Systems\s*Centre)\b",
        r"\b(VSSC|Vikram\s*Sarabhai\s*Space\s*Centre)\b",
        r"\b(SDSC|Satish\s*Dhawan\s*Space\s*Centre)\b",
        r"\b(IIST|Indian\s*Institute\s*of\s*Space\s*Science\s*and\s*Technology)\b",
        r"\b(SHAR|Sriharikota\s*Range)\b",
        r"\b(ISTRAC|ISRO\s*Telemetry\s*Tracking\s*and\s*Command)\b"
    ]
    for pattern in org_patterns:
        org_matches = re.findall(pattern, text, re.IGNORECASE)
        entities["Organization"].update(org_matches)
    
    # Countries
    country_patterns = [
        r"\b(India|Indian)\b",
        r"\b(United\s*States|USA|US)\b",
        r"\b(Russia|Russian)\b",
        r"\b(Japan|Japanese)\b",
        r"\b(Europe|European)\b",
        r"\b(China|Chinese)\b"
    ]
    for pattern in country_patterns:
        country_matches = re.findall(pattern, text, re.IGNORECASE)
        entities["Country"].update(country_matches)
    
    # Research Areas - AI, Propulsion, Materials, Robotics, etc.
    research_patterns = [
        r"\b(Artificial\s*Intelligence|Machine\s*Learning|Deep\s*Learning|AI|ML)\b",
        r"\b(Propulsion|Rocket\s*Science|Combustion|Thermal)\b",
        r"\b(Materials\s*Science|Composite|Alloy|Polymer)\b",
        r"\b(Robotics|Autonomous\s*Systems|Rover|Lander)\b",
        r"\b(Satellite\s*Design|Spacecraft\s*Design|Payload\s*Design)\b",
        r"\b(Orbital\s*Mechanics|Trajectory|Orbit|Astrodynamics)\b",
        r"\b(Thermal\s*Management|Heat\s*Transfer|Cryogenic)\b",
        r"\b(Power\s*Systems|Solar\s*Panel|Battery|Energy)\b",
        r"\b(Communication\s*Systems|Antenna|Signal|Transmission)\b",
        r"\b(Remote\s*Sensing|Earth\s*Observation|Imaging|Spectroscopy)\b"
    ]
    for pattern in research_patterns:
        research_matches = re.findall(pattern, text, re.IGNORECASE)
        entities["ResearchArea"].update(research_matches)
    
    # Technologies - Specific technical innovations
    tech_patterns = [
        r"\b(Cryogenic\s*Engine|Cryogenic\s*Technology)\b",
        r"\b(Composite\s*Materials|Carbon\s*Fiber|Kevlar)\b",
        r"\b(Solar\s*Panel|Photovoltaic|PV\s*Cell)\b",
        r"\b(Ion\s*Thruster|Electric\s*Propulsion|Hall\s*Effect)\b",
        r"\b(Autonomous\s*Navigation|GPS|GNSS|Navigation\s*System)\b",
        r"\b(Thermal\s*Control\s*System|TCS|Radiator)\b",
        r"\b(Power\s*Management\s*Unit|PMU|Power\s*Distribution)\b",
        r"\b(Communication\s*Payload|Transponder|Transceiver)\b",
        r"\b(Attitude\s*Control\s*System|ACS|Reaction\s*Wheel)\b",
        r"\b(Structural\s*Design|Frame|Chassis|Bus)\b"
    ]
    for pattern in tech_patterns:
        tech_matches = re.findall(pattern, text, re.IGNORECASE)
        entities["Technology"].update(tech_matches)
    
    # Partnerships - Collaborations and partnerships
    partnership_patterns = [
        r"\b(ISRO[-\s]?Industry\s*Partnership|Industry\s*Collaboration)\b",
        r"\b(ISRO[-\s]?Academia|Academic\s*Partnership|University\s*Collaboration)\b",
        r"\b(International\s*Collaboration|International\s*Partnership|Joint\s*Mission)\b",
        r"\b(Government\s*Agency|Ministry|Department)\b",
        r"\b(Private\s*Company|Industry\s*Partner|Commercial\s*Partner)\b",
        r"\b(Research\s*Institute|Think\s*Tank|Laboratory)\b",
        r"\b(Technology\s*Transfer|Licensing\s*Agreement|Joint\s*Development)\b"
    ]
    for pattern in partnership_patterns:
        partnership_matches = re.findall(pattern, text, re.IGNORECASE)
        entities["Partnership"].update(partnership_matches)
    
    # Publications - Research papers and reports
    pub_patterns = [
        r"\b(Research\s*Paper|Technical\s*Report|White\s*Paper|Publication)\b",
        r"\b(Journal\s*Article|Conference\s*Paper|Proceedings)\b",
        r"\b(Annual\s*Report|Technical\s*Document|Brochure)\b",
        r"\b(SSRN|arXiv|IEEE|ACM)\b"
    ]
    for pattern in pub_patterns:
        pub_matches = re.findall(pattern, text, re.IGNORECASE)
        entities["Publication"].update(pub_matches)
    
    # Patents - Technology patents and innovations
    patent_patterns = [
        r"\b(Patent|Patented|Patent\s*Pending|Intellectual\s*Property|IP)\b",
        r"\b(Innovation|Proprietary|Proprietary\s*Technology|Trade\s*Secret)\b",
        r"\b(Technology\s*License|Licensed\s*Technology|Licensing)\b"
    ]
    for pattern in patent_patterns:
        patent_matches = re.findall(pattern, text, re.IGNORECASE)
        entities["Patent"].update(patent_matches)

    return entities

def populate_database(deep_indexing=False):
    folders = [
        "data/isro_docs",
        "data/isro_docs_large"
    ]
    
    llm_extractor = None
    if deep_indexing:
        print("Initializing LLM Entity Extractor for Domain Adaptation...")
        llm_extractor = LLMEntityExtractor()
    
    all_docs = []
    for folder_path in folders:
        print(f"Loading documents from {folder_path}...")
        docs = load_documents(folder_path)
        if docs:
            print(f"  Loaded {len(docs)} documents from {folder_path}.")
            all_docs.extend(docs)
        else:
            print(f"  No documents found in {folder_path}.")

    if not all_docs:
        print("No documents found across any folder.")
        return

    print(f"Total documents loaded: {len(all_docs)}")

    # 1. Populate Vector Store
    print("Splitting documents...")
    # Assign access levels based on filename for RBAC
    for doc in all_docs:
        source = doc.metadata.get("source", "").lower()
        if "gslv" in source or "lvm3" in source:
            doc.metadata["access_level"] = "technical"
        elif "classified" in source:
            doc.metadata["access_level"] = "classified"
        else:
            doc.metadata["access_level"] = "public"

    chunks = split_documents(all_docs)
    print(f"Created {len(chunks)} chunks.")

    print("Creating Vector Store (FAISS)...")
    create_vector_store(chunks)
    print("Vector Store created and saved.")

    # 2. Populate Knowledge Graph
    print("Connecting to Knowledge Graph (Neo4j)...")
    try:
        graph = GraphStore()
        graph.setup_schema()
        
        print("Extracting entities and populating Graph...")
        
        # Track all extracted entities across documents for relationship building
        all_extracted = {
            "Mission": set(),
            "LaunchVehicle": set(),
            "Stage": set(),
            "Engine": set(),
            "Payload": set(),
            "Organization": set(),
            "Country": set(),
            "ResearchArea": set(),
            "Technology": set(),
            "Partnership": set(),
            "Publication": set(),
            "Patent": set()
        }
        
        # Document-level entity tracking for co-occurrence relationships
        doc_entities = []
        
        for doc in all_docs:
            text = doc.page_content
            source = doc.metadata.get("source", "")
            
            # Use LLM extracted entities if deep_indexing is ON, else fallback to Regex
            if deep_indexing and llm_extractor:
                extracted = llm_extractor.extract(text)
                # Merge with regex for robustness
                reg_extracted = extract_entities(text)
                for k in extracted:
                    extracted[k].update(reg_extracted[k])
            else:
                extracted = extract_entities(text)
            
            # Track entities for this document
            doc_entities.append({
                "source": source,
                "entities": extracted
            })
            
            # Update global entity tracking
            for entity_type, entities in extracted.items():
                all_extracted[entity_type].update(entities)
            
            # Add all entity types to graph
            for mission in extracted["Mission"]:
                graph.add_entity("Mission", {"name": mission, "source": source})
            
            for lv in extracted["LaunchVehicle"]:
                graph.add_entity("LaunchVehicle", {"name": lv, "source": source})
            
            for stage in extracted["Stage"]:
                graph.add_entity("Stage", {"name": stage, "source": source})

            for engine in extracted["Engine"]:
                graph.add_entity("Engine", {"name": engine, "source": source})
            
            for payload in extracted["Payload"]:
                graph.add_entity("Payload", {"name": payload, "source": source})
            
            for org in extracted["Organization"]:
                graph.add_entity("Organization", {"name": org, "source": source})
            
            for country in extracted["Country"]:
                graph.add_entity("Country", {"name": country, "source": source})
            
            for research_area in extracted["ResearchArea"]:
                graph.add_entity("ResearchArea", {"name": research_area, "source": source})
            
            for tech in extracted["Technology"]:
                graph.add_entity("Technology", {"name": tech, "source": source})
            
            for partnership in extracted["Partnership"]:
                graph.add_entity("Partnership", {"name": partnership, "source": source})
            
            for pub in extracted["Publication"]:
                graph.add_entity("Publication", {"name": pub, "source": source})
            
            for patent in extracted["Patent"]:
                graph.add_entity("Patent", {"name": patent, "source": source})
        
        print(f"Added {sum(len(v) for v in all_extracted.values())} unique entities to graph")
        
        # Create comprehensive relationships based on co-occurrence in documents
        print("Creating relationships between entities...")
        relationship_count = 0
        
        for doc_idx, doc_data in enumerate(doc_entities):
            entities = doc_data["entities"]
            print(f"  Processing document {doc_idx + 1}/{len(doc_entities)}...")
            
            # Mission relationships
            for mission in entities["Mission"]:
                # Mission uses LaunchVehicle
                for lv in entities["LaunchVehicle"]:
                    try:
                        graph.add_relationship("Mission", mission, "LaunchVehicle", lv, "USES_LAUNCH_VEHICLE")
                        relationship_count += 1
                    except Exception as e:
                        print(f"    Warning: Could not create relationship {mission} -> {lv}: {e}")
                
                # Mission has Payload
                for payload in entities["Payload"]:
                    try:
                        graph.add_relationship("Mission", mission, "Payload", payload, "HAS_PAYLOAD")
                        relationship_count += 1
                    except Exception as e:
                        print(f"    Warning: Could not create relationship {mission} -> {payload}: {e}")
                
                # Mission conducted by Organization
                for org in entities["Organization"]:
                    try:
                        graph.add_relationship("Mission", mission, "Organization", org, "CONDUCTED_BY")
                        relationship_count += 1
                    except Exception as e:
                        print(f"    Warning: Could not create relationship {mission} -> {org}: {e}")
                
                # Mission from Country
                for country in entities["Country"]:
                    try:
                        graph.add_relationship("Mission", mission, "Country", country, "FROM_COUNTRY")
                        relationship_count += 1
                    except Exception as e:
                        print(f"    Warning: Could not create relationship {mission} -> {country}: {e}")
            
            # LaunchVehicle relationships
            for lv in entities["LaunchVehicle"]:
                # LaunchVehicle has Stage
                for stage in entities["Stage"]:
                    try:
                        graph.add_relationship("LaunchVehicle", lv, "Stage", stage, "HAS_STAGE")
                        relationship_count += 1
                    except Exception as e:
                        print(f"    Warning: Could not create relationship {lv} -> {stage}: {e}")
                
                # LaunchVehicle uses Engine
                for engine in entities["Engine"]:
                    try:
                        graph.add_relationship("LaunchVehicle", lv, "Engine", engine, "USES_ENGINE")
                        relationship_count += 1
                    except Exception as e:
                        print(f"    Warning: Could not create relationship {lv} -> {engine}: {e}")
                
                # LaunchVehicle built by Organization
                for org in entities["Organization"]:
                    try:
                        graph.add_relationship("LaunchVehicle", lv, "Organization", org, "BUILT_BY")
                        relationship_count += 1
                    except Exception as e:
                        print(f"    Warning: Could not create relationship {lv} -> {org}: {e}")
            
            # Stage relationships
            for stage in entities["Stage"]:
                # Stage uses Engine
                for engine in entities["Engine"]:
                    try:
                        graph.add_relationship("Stage", stage, "Engine", engine, "USES_ENGINE")
                        relationship_count += 1
                    except Exception as e:
                        print(f"    Warning: Could not create relationship {stage} -> {engine}: {e}")
            
            # Payload relationships
            for payload in entities["Payload"]:
                # Payload built by Organization
                for org in entities["Organization"]:
                    try:
                        graph.add_relationship("Payload", payload, "Organization", org, "BUILT_BY")
                        relationship_count += 1
                    except Exception as e:
                        print(f"    Warning: Could not create relationship {payload} -> {org}: {e}")
            
            # Organization relationships
            for org in entities["Organization"]:
                # Organization from Country
                for country in entities["Country"]:
                    try:
                        graph.add_relationship("Organization", org, "Country", country, "FROM_COUNTRY")
                        relationship_count += 1
                    except Exception as e:
                        print(f"    Warning: Could not create relationship {org} -> {country}: {e}")
            
            # NEW: Research Area relationships
            for research_area in entities["ResearchArea"]:
                # Organization researches ResearchArea
                for org in entities["Organization"]:
                    try:
                        graph.add_relationship("Organization", org, "ResearchArea", research_area, "RESEARCHES")
                        relationship_count += 1
                    except Exception as e:
                        pass
                
                # Mission involves ResearchArea
                for mission in entities["Mission"]:
                    try:
                        graph.add_relationship("Mission", mission, "ResearchArea", research_area, "INVOLVES")
                        relationship_count += 1
                    except Exception as e:
                        pass
            
            # NEW: Technology relationships
            for tech in entities["Technology"]:
                # Organization develops Technology
                for org in entities["Organization"]:
                    try:
                        graph.add_relationship("Organization", org, "Technology", tech, "DEVELOPS")
                        relationship_count += 1
                    except Exception as e:
                        pass
                
                # Mission uses Technology
                for mission in entities["Mission"]:
                    try:
                        graph.add_relationship("Mission", mission, "Technology", tech, "USES_TECHNOLOGY")
                        relationship_count += 1
                    except Exception as e:
                        pass
                
                # LaunchVehicle uses Technology
                for lv in entities["LaunchVehicle"]:
                    try:
                        graph.add_relationship("LaunchVehicle", lv, "Technology", tech, "USES_TECHNOLOGY")
                        relationship_count += 1
                    except Exception as e:
                        pass
                
                # Payload uses Technology
                for payload in entities["Payload"]:
                    try:
                        graph.add_relationship("Payload", payload, "Technology", tech, "USES_TECHNOLOGY")
                        relationship_count += 1
                    except Exception as e:
                        pass
            
            # NEW: Partnership relationships
            for partnership in entities["Partnership"]:
                # Organization has Partnership
                for org in entities["Organization"]:
                    try:
                        graph.add_relationship("Organization", org, "Partnership", partnership, "HAS_PARTNERSHIP")
                        relationship_count += 1
                    except Exception as e:
                        pass
            
            # NEW: Publication relationships
            for pub in entities["Publication"]:
                # Organization publishes Publication
                for org in entities["Organization"]:
                    try:
                        graph.add_relationship("Organization", org, "Publication", pub, "PUBLISHES")
                        relationship_count += 1
                    except Exception as e:
                        pass
                
                # Mission documented in Publication
                for mission in entities["Mission"]:
                    try:
                        graph.add_relationship("Mission", mission, "Publication", pub, "DOCUMENTED_IN")
                        relationship_count += 1
                    except Exception as e:
                        pass
            
            # NEW: Patent relationships
            for patent in entities["Patent"]:
                # Organization holds Patent
                for org in entities["Organization"]:
                    try:
                        graph.add_relationship("Organization", org, "Patent", patent, "HOLDS_PATENT")
                        relationship_count += 1
                    except Exception as e:
                        pass
                
                # Technology protected by Patent
                for tech in entities["Technology"]:
                    try:
                        graph.add_relationship("Technology", tech, "Patent", patent, "PROTECTED_BY")
                        relationship_count += 1
                    except Exception as e:
                        pass

        print(f"Created {relationship_count} relationships in the Knowledge Graph")
        
        # Print summary statistics
        total_nodes = graph.count_nodes()
        print(f"\nKnowledge Graph Summary:")
        print(f"  Total Nodes: {total_nodes}")
        print(f"  Missions: {len(all_extracted['Mission'])}")
        print(f"  Launch Vehicles: {len(all_extracted['LaunchVehicle'])}")
        print(f"  Stages: {len(all_extracted['Stage'])}")
        print(f"  Engines: {len(all_extracted['Engine'])}")
        print(f"  Payloads: {len(all_extracted['Payload'])}")
        print(f"  Organizations: {len(all_extracted['Organization'])}")
        print(f"  Countries: {len(all_extracted['Country'])}")
        print(f"  Research Areas: {len(all_extracted['ResearchArea'])}")
        print(f"  Technologies: {len(all_extracted['Technology'])}")
        print(f"  Partnerships: {len(all_extracted['Partnership'])}")
        print(f"  Publications: {len(all_extracted['Publication'])}")
        print(f"  Patents: {len(all_extracted['Patent'])}")
        print(f"  Total Relationships: {relationship_count}")
        
        graph.close()
        print("\nKnowledge Graph populated successfully.")
    except Exception as e:
        print(f"Skipping Graph Population due to error (is Neo4j running?): {e}")

if __name__ == "__main__":
    populate_database()
