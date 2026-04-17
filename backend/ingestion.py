import os
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from backend.graph_store import GraphStore
import re

def load_documents(folder_path):
    documents = []

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        return []

    for file in os.listdir(folder_path):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(folder_path, file)
            reader = PdfReader(pdf_path)

            text = ""
            for page in reader.pages:
                text += (page.extract_text() or "") + " \n"

            # Create a Document object with metadata
            security_level = "classified" if any(k in file.lower() for k in ["spec", "classified", "restricted", "internal", "propulsion", "fuel"]) else "public"
            doc = Document(page_content=text, metadata={"source": file, "security_level": security_level})
            documents.append(doc)

    return documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )

    chunks = []
    graph = GraphStore()
    
    for doc in documents:
        # split_documents method handles list of Documents and preserves metadata
        doc_chunks = splitter.split_documents([doc])
        for chunk in doc_chunks:
            # 1. Extract entities for each chunk
            entities = extract_domain_entities(chunk.page_content)
            chunk.metadata["entities"] = entities
            
            # 2. Automated Graph Population
            # Add entities to graph
            for entity in entities:
                # Basic label mapping
                label = "Mission" # Default
                if any(k in entity.upper() for k in ["PSLV", "GSLV", "LVM3"]):
                    label = "LaunchVehicle"
                elif any(k in entity.upper() for k in ["GSAT", "EOS", "CARTOSAT"]):
                    label = "Satellite"
                
                graph.add_entity(label, {"name": entity, "source": doc.metadata["source"]})
            
            # 3. Relationship Extraction (Co-occurrence Heuristic)
            if len(entities) >= 2:
                # Link all entities found in the same chunk
                for i in range(len(entities)):
                    for j in range(i + 1, len(entities)):
                        e1, e2 = entities[i], entities[j]
                        # Create generic relevant_to link
                        graph.add_relationship("Mission", e1, "Mission", e2, "RELATED_TO")
        
        chunks.extend(doc_chunks)

    graph.close()
    return chunks

def extract_domain_entities(text):
    """
    Automated Entity Extraction for ISRO domain.
    """
    patterns = [
        r"PSLV\s*[CDV]?\d*", 
        r"GSLV\s*(?:Mk\s*III|Mk\s*II|LVM3|F\d+)?", 
        r"LVM\d+",
        r"Chandrayaan\s*-\s*\d+", 
        r"Gaganyaan", 
        r"GSAT\s*-\s*\d+[A-Z]?",
        r"EOS\s*-\s*\d+",
        r"Cartosat\s*-\s*\d+[A-Z]?",
        r"RISAT\s*-\s*\d+[A-Z]?",
        r"Aditya\s*-\s*L\d",
        r"NISAR",
        r"CMS\s*-\s*\d+",
        r"Vikram\s*-\s*[S1]",
        r"Arianespace",
        r"Kourou",
        r"Sriharikota",
        r"SDSC",
        r"VSSC",
        r"LPSC",
        r"IPRC"
    ]
    entities = []
    for p in patterns:
        matches = re.findall(p, text, re.IGNORECASE)
        entities.extend(matches)
    return list(set(entities))
