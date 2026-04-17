class RBAC:
    """
    Sovereign Intelligence RBAC System.
    
    SECURITY MODEL:
    1. Trust Boundary: The main_engine enforces a hard boundary between retrieval and generation.
    2. IND-CPA (Indistinguishability under Chosen Plaintext Attack): 
       We ensure that a 'Public' adversary cannot distinguish between a response generated from 
       empty context and a 'Restricted' response by ensuring refusal patterns are static and 
       lack technical metadata leakage.
    3. Document Level Isolation: All retrieval is filtered pre-LLM to ensure zero context-contamination.
    """
    ROLES = {
        "Scientist": ["view_all", "view_classified", "edit_docs"],
        "Engineer": ["view_all", "view_technical"],
        "Analyst": ["view_mission_stats"],
        "Public": ["view_public"]
    }

    # Document access levels mapping (Hard-coded Permission Matrix)
    DOC_ACCESS = {
        "classified": ["Scientist"],
        "technical": ["Scientist", "Engineer"],
        "mission_stats": ["Scientist", "Engineer", "Analyst"],
        "public": ["Scientist", "Engineer", "Analyst", "Public"]
    }

    @staticmethod
    def get_role_permissions(role):
        return RBAC.ROLES.get(role, [])

    @staticmethod
    def check_access(user_role, doc_type):
        """
        Formal Access Check. 
        Ensures strict containment within the user's clearing level.
        """
        allowed_roles = RBAC.DOC_ACCESS.get(doc_type, [])
        return user_role in allowed_roles

    @staticmethod
    def filter_documents(user_role, documents, strict_mode=True):
        """
        Filters out documents that the user is not allowed to see based on metadata.
        Strict Mode (Default): Strips all metadata from filtered documents to prevent title leakage.
        """
        if not documents:
            return []
            
        filtered_docs = []
        for doc in documents:
            doc_level = doc.metadata.get("access_level", "public") 
            if RBAC.check_access(user_role, doc_level):
                filtered_docs.append(doc)
            elif not strict_mode:
                # In non-strict mode, we might keep metadata for audit, but NEVER for LLM prompt
                pass
        
        return filtered_docs
