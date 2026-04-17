"""
Hallucination Scorer - Rates responses on 0-3 scale
0 = No hallucinations (all facts verified)
1 = Minor hallucinations (1-2 unverified claims)
2 = Moderate hallucinations (3-5 unverified claims)
3 = Significant hallucinations (6+ unverified claims)
"""

import re
from backend.validator import Validator

class HallucinationScorer:
    def __init__(self):
        self.validator = Validator()
        # Known facts about Indian space program
        self.known_facts = {
            "pslv": {
                "stages": 4,
                "payload_leo": 1600,  # kg
                "payload_geo": 1000,  # kg
                "engines": ["vikas", "solid"],
                "cryogenic": False,
                "crewed": False,
            },
            "gslv": {
                "stages": 3,
                "payload_geo": 2000,  # kg
                "engines": ["vikas", "cryogenic"],
                "cryogenic": True,
                "nuclear": False,
                "crewed": False,
            },
            "chandrayaan-1": {
                "type": "orbiter",
                "lander": False,
                "year": 2008,
            },
            "chandrayaan-2": {
                "type": "orbiter+lander",
                "lander": True,
            },
            "chandrayaan-3": {
                "type": "lander",
                "lander": True,
            },
        }
    
    def score_response(self, query, response):
        """
        Score a response for hallucinations on 0-3 scale
        Returns: (score, details)
        """
        # First, check if validator flags it as invalid
        is_valid, validation_msg = self.validator.validate_answer(query, response)
        
        if not is_valid:
            # Validator found a hallucination
            return 3, f"Hallucination detected: {validation_msg}"
        
        # If valid, check for unverified claims
        score = self._calculate_unverified_claims(query, response)
        
        if score == 0:
            return 0, "No hallucinations detected - all claims verified"
        elif score == 1:
            return 1, "Minor hallucinations - 1-2 unverified claims"
        elif score == 2:
            return 2, "Moderate hallucinations - 3-5 unverified claims"
        else:
            return 3, "Significant hallucinations - 6+ unverified claims"
    
    def _calculate_unverified_claims(self, query, response):
        """
        Count unverified claims in response
        """
        unverified_count = 0
        
        # 1. Check for known false claims
        false_claims = self._detect_false_claims(response)
        unverified_count += false_claims
        
        # 2. Check for incorrect acronym definitions
        if re.search(r"gslv.*global\s+space\s+launch", response, re.IGNORECASE):
            unverified_count += 1  # GSLV is Geosynchronous, not Global
        
        # 3. Check for vague claims without specifics
        vague_patterns = [
            r"it is believed that",
            r"some say",
            r"allegedly",
            r"rumor has it",
            r"supposedly",
            r"it is thought",
        ]
        
        for pattern in vague_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                unverified_count += 1
        
        # 4. Check for unsupported technical claims (numerical hallucinations)
        numerical_hallucinations = self._detect_numerical_hallucinations(response)
        unverified_count += numerical_hallucinations
        
        # 5. Check for contradictions within response (HIGH WEIGHT)
        if self._has_internal_contradictions(response):
            unverified_count += 3  # Self-contradictions are major hallucinations
        
        # 6. Check for overgeneralizations
        if self._has_overgeneralization(response):
            unverified_count += 2  # Overgeneralizations are serious
        
        return min(int(unverified_count), 3)
    
    def _detect_false_claims(self, response):
        """
        Detect known false claims about space missions
        """
        count = 0
        
        false_patterns = [
            (r"pslv.*cryogenic", "PSLV doesn't use cryogenic engines"),
            (r"gslv.*nuclear", "GSLV doesn't use nuclear propulsion"),
            (r"chandrayaan-1.*lander", "Chandrayaan-1 was an orbiter, not a lander"),
            (r"pslv.*crew", "PSLV is unmanned"),
            (r"pslv.*2000\s*kg.*geo", "PSLV can't carry 2000kg to GEO"),
            (r"pslv.*5000\s*kg", "PSLV can't carry 5000kg"),
            (r"gslv.*x5", "GSLV-X5 doesn't exist"),
            (r"pslv-ultra", "PSLV-Ultra doesn't exist"),
            (r"z-omega", "Z-Omega mission doesn't exist"),
            (r"nasa.*pslv", "PSLV was not developed by NASA"),
            (r"quantum.*computing.*navigation", "Quantum computing not used in navigation"),
            (r"mars.*pslv", "PSLV cannot travel to Mars"),
            (r"pslv.*10\s*stages", "PSLV doesn't have 10 stages"),
        ]
        
        for pattern, msg in false_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                count += 1
        
        return count
    
    def _detect_numerical_hallucinations(self, response):
        """
        Detect incorrect numerical claims
        """
        count = 0
        
        # Check for incorrect payload capacities
        if re.search(r"pslv.*(?:carry|payload).*(\d+)\s*kg.*geo", response, re.IGNORECASE):
            match = re.search(r"pslv.*(?:carry|payload).*(\d+)\s*kg.*geo", response, re.IGNORECASE)
            if match:
                kg = int(match.group(1))
                if kg > 1000:  # PSLV GEO capacity is ~1000kg
                    count += 1
        
        if re.search(r"pslv.*(?:carry|payload).*(\d+)\s*kg.*leo", response, re.IGNORECASE):
            match = re.search(r"pslv.*(?:carry|payload).*(\d+)\s*kg.*leo", response, re.IGNORECASE)
            if match:
                kg = int(match.group(1))
                if kg > 1600:  # PSLV LEO capacity is ~1600kg
                    count += 1
        
        # Check for extreme payload claims (5000kg, 3000kg to GEO)
        if re.search(r"pslv.*(?:carry|payload).*(\d+)\s*kg", response, re.IGNORECASE):
            match = re.search(r"pslv.*(?:carry|payload).*(\d+)\s*kg", response, re.IGNORECASE)
            if match:
                kg = int(match.group(1))
                if kg >= 3000:  # Extreme claim
                    count += 1
        
        return count
    
    def _has_internal_contradictions(self, response):
        """
        Check if response contradicts itself
        """
        # Check for direct contradictions
        contradictions = [
            (r"pslv.*is.*launch.*vehicle.*pslv.*is not.*launch", "contradicts itself"),
            (r"is\s+a\s+.*\.\s+.*is\s+not\s+a\s+", "contradicts itself"),
            (r"is\s+not\s+a\s+.*\.\s+.*is\s+a\s+", "contradicts itself"),
            (r"doesn't.*does\s", "contradicts itself"),
            (r"never.*always", "contradicts itself"),
        ]
        
        for pattern, _ in contradictions:
            if re.search(pattern, response, re.IGNORECASE):
                return True
        
        return False
    
    def _has_overgeneralization(self, response):
        """
        Check for overgeneralizations that are false
        """
        # "All Indian launch vehicles use cryogenic engines" - FALSE
        if re.search(r"all.*(?:indian|isro).*launch.*vehicle.*cryogenic", response, re.IGNORECASE):
            return True
        
        if re.search(r"all.*(?:indian|isro).*mission.*(?:nuclear|cryogenic)", response, re.IGNORECASE):
            return True
        
        return False
