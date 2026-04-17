"""
NEXORA Aerospace Helper Module
Provides problem-solving assistance for aerospace missions and engineering challenges
while maintaining accuracy and logical correctness
"""

import re
from typing import List, Dict, Tuple
from backend.graph_store import GraphStore

class AerospaceHelper:
    """
    Aerospace problem-solving helper that provides:
    - Mission planning assistance
    - Technical problem-solving
    - Design recommendations
    - Logical reasoning for aerospace challenges
    """
    
    def __init__(self):
        self.graph_store = None
        try:
            self.graph_store = GraphStore()
            if self.graph_store.verify_connectivity():
                print("[AerospaceHelper] Graph Store connected for aerospace reasoning")
            else:
                print("[AerospaceHelper] Graph Store unavailable - basic mode")
        except Exception as e:
            print(f"[AerospaceHelper] Warning: {e}")
    
    def analyze_mission_requirements(self, mission_description: str) -> Dict:
        """
        Analyzes mission requirements and suggests appropriate vehicles/configurations
        
        Args:
            mission_description: Description of the mission (e.g., "Need to launch 2000kg to GTO")
        
        Returns:
            Dict with mission analysis, recommendations, and reasoning
        """
        analysis = {
            "mission_type": None,
            "payload_mass": None,
            "target_orbit": None,
            "recommended_vehicles": [],
            "reasoning": [],
            "constraints": [],
            "alternatives": []
        }
        
        # Extract mission parameters
        payload_match = re.search(r'(\d+)\s*kg', mission_description, re.IGNORECASE)
        if payload_match:
            analysis["payload_mass"] = int(payload_match.group(1))
        
        # Identify orbit type
        orbit_keywords = {
            "LEO": ["low earth orbit", "leo", "400 km", "500 km"],
            "GTO": ["geostationary transfer", "gto", "36000 km"],
            "GSO": ["geostationary", "gso", "stationary orbit"],
            "SSO": ["sun-synchronous", "sso", "polar"],
            "HEO": ["highly elliptical", "heo"],
        }
        
        for orbit, keywords in orbit_keywords.items():
            if any(kw in mission_description.lower() for kw in keywords):
                analysis["target_orbit"] = orbit
                break
        
        # Recommend vehicles based on payload and orbit
        if analysis["payload_mass"] and analysis["target_orbit"]:
            recommendations = self._recommend_vehicles(
                analysis["payload_mass"],
                analysis["target_orbit"]
            )
            analysis["recommended_vehicles"] = recommendations["vehicles"]
            analysis["reasoning"] = recommendations["reasoning"]
            analysis["constraints"] = recommendations["constraints"]
            analysis["alternatives"] = recommendations["alternatives"]
        
        return analysis
    
    def _recommend_vehicles(self, payload_mass: int, target_orbit: str) -> Dict:
        """
        Recommends launch vehicles based on payload and orbit
        """
        recommendations = {
            "vehicles": [],
            "reasoning": [],
            "constraints": [],
            "alternatives": []
        }
        
        # PSLV capabilities
        pslv_leo_capacity = 1600  # kg to LEO
        pslv_sso_capacity = 1200  # kg to SSO
        
        # GSLV capabilities
        gslv_gto_capacity = 2500  # kg to GTO
        gslv_leo_capacity = 5000  # kg to LEO
        
        # LVM3 capabilities
        lvm3_gto_capacity = 4000  # kg to GTO
        lvm3_leo_capacity = 8000  # kg to LEO
        
        if target_orbit == "LEO":
            if payload_mass <= pslv_leo_capacity:
                recommendations["vehicles"].append({
                    "name": "PSLV",
                    "capacity": pslv_leo_capacity,
                    "margin": pslv_leo_capacity - payload_mass,
                    "cost_effective": True,
                    "reliability": "Proven (50+ launches)"
                })
                recommendations["reasoning"].append(
                    f"PSLV can carry {payload_mass}kg to LEO with {pslv_leo_capacity - payload_mass}kg margin"
                )
            
            if payload_mass <= gslv_leo_capacity:
                recommendations["vehicles"].append({
                    "name": "GSLV Mk III (LVM3)",
                    "capacity": gslv_leo_capacity,
                    "margin": gslv_leo_capacity - payload_mass,
                    "cost_effective": False,
                    "reliability": "Proven (10+ launches)"
                })
                recommendations["reasoning"].append(
                    f"GSLV Mk III can carry {payload_mass}kg to LEO with significant margin"
                )
            
            if payload_mass > gslv_leo_capacity:
                recommendations["constraints"].append(
                    f"Payload {payload_mass}kg exceeds GSLV Mk III LEO capacity ({gslv_leo_capacity}kg)"
                )
                recommendations["alternatives"].append(
                    "Consider splitting payload into multiple launches or using international launch services"
                )
        
        elif target_orbit == "GTO":
            if payload_mass <= gslv_gto_capacity:
                recommendations["vehicles"].append({
                    "name": "GSLV Mk II",
                    "capacity": gslv_gto_capacity,
                    "margin": gslv_gto_capacity - payload_mass,
                    "cost_effective": True,
                    "reliability": "Proven (15+ launches)"
                })
                recommendations["reasoning"].append(
                    f"GSLV Mk II can carry {payload_mass}kg to GTO with {gslv_gto_capacity - payload_mass}kg margin"
                )
            
            if payload_mass <= lvm3_gto_capacity:
                recommendations["vehicles"].append({
                    "name": "GSLV Mk III (LVM3)",
                    "capacity": lvm3_gto_capacity,
                    "margin": lvm3_gto_capacity - payload_mass,
                    "cost_effective": False,
                    "reliability": "Proven (10+ launches)"
                })
                recommendations["reasoning"].append(
                    f"GSLV Mk III can carry {payload_mass}kg to GTO with {lvm3_gto_capacity - payload_mass}kg margin"
                )
            
            if payload_mass > lvm3_gto_capacity:
                recommendations["constraints"].append(
                    f"Payload {payload_mass}kg exceeds GSLV Mk III GTO capacity ({lvm3_gto_capacity}kg)"
                )
        
        elif target_orbit == "SSO":
            if payload_mass <= pslv_sso_capacity:
                recommendations["vehicles"].append({
                    "name": "PSLV",
                    "capacity": pslv_sso_capacity,
                    "margin": pslv_sso_capacity - payload_mass,
                    "cost_effective": True,
                    "reliability": "Proven (50+ launches)"
                })
                recommendations["reasoning"].append(
                    f"PSLV is ideal for SSO missions, can carry {payload_mass}kg with {pslv_sso_capacity - payload_mass}kg margin"
                )
        
        return recommendations
    
    def solve_aerospace_problem(self, problem_description: str, context_data: List[str] = None) -> Dict:
        """
        Solves aerospace engineering problems using logical reasoning
        
        Args:
            problem_description: Description of the aerospace problem
            context_data: Optional context from RAG system
        
        Returns:
            Dict with problem analysis, solution, and reasoning
        """
        solution = {
            "problem_type": None,
            "analysis": [],
            "solution": [],
            "reasoning": [],
            "constraints": [],
            "recommendations": [],
            "references": context_data or []
        }
        
        # Identify problem type - check in order of specificity
        problem_lower = problem_description.lower()
        
        # Check for design problems first (most specific)
        if any(word in problem_lower for word in ["design", "configuration", "structure", "build", "create"]):
            solution["problem_type"] = "Design & Configuration"
            solution = self._solve_design_problem(problem_description, solution)
        
        # Check for propulsion problems
        elif any(word in problem_lower for word in ["propulsion", "propellant", "engine", "thrust", "delta-v"]):
            solution["problem_type"] = "Propulsion & Energy"
            solution = self._solve_propulsion_problem(problem_description, solution)
        
        # Check for orbital problems
        elif any(word in problem_lower for word in ["orbit", "altitude", "trajectory", "orbital"]):
            solution["problem_type"] = "Orbital Mechanics"
            solution = self._solve_orbital_problem(problem_description, solution)
        
        # Check for payload problems
        elif any(word in problem_lower for word in ["payload", "mass", "weight", "capacity", "optimize"]):
            solution["problem_type"] = "Payload Optimization"
            solution = self._solve_payload_problem(problem_description, solution)
        
        # Check for mission planning
        elif any(word in problem_lower for word in ["mission", "planning", "schedule", "launch", "plan"]):
            solution["problem_type"] = "Mission Planning"
            solution = self._solve_mission_planning_problem(problem_description, solution)
        
        return solution
    
    def _solve_payload_problem(self, problem: str, solution: Dict) -> Dict:
        """Solves payload-related problems"""
        solution["analysis"].append("Analyzing payload constraints and optimization opportunities")
        
        # Extract payload mass if mentioned
        mass_match = re.search(r'(\d+)\s*kg', problem, re.IGNORECASE)
        if mass_match:
            payload_mass = int(mass_match.group(1))
            solution["analysis"].append(f"Payload mass: {payload_mass}kg")
            
            # Provide optimization recommendations
            solution["recommendations"].append(
                f"For {payload_mass}kg payload, consider:"
            )
            solution["recommendations"].append(
                "1. Material optimization - use composite materials to reduce mass by 15-20%"
            )
            solution["recommendations"].append(
                "2. Component consolidation - integrate multiple functions into single units"
            )
            solution["recommendations"].append(
                "3. Redundancy analysis - eliminate non-critical redundancy"
            )
            
            solution["solution"].append(
                f"Optimized payload mass could be reduced to {int(payload_mass * 0.85)}kg with proper engineering"
            )
        
        solution["reasoning"].append(
            "Payload optimization follows aerospace engineering principles of mass reduction while maintaining functionality"
        )
        
        return solution
    
    def _solve_orbital_problem(self, problem: str, solution: Dict) -> Dict:
        """Solves orbital mechanics problems"""
        solution["analysis"].append("Analyzing orbital mechanics and trajectory requirements")
        
        # Identify orbit type
        if "leo" in problem.lower() or "low earth" in problem.lower():
            solution["analysis"].append("Target: Low Earth Orbit (LEO)")
            solution["recommendations"].append("LEO characteristics: 200-2000 km altitude, ~90 minute orbital period")
            solution["recommendations"].append("Advantages: Lower launch energy, faster access to space")
            solution["recommendations"].append("Disadvantages: Atmospheric drag, shorter mission life")
        
        elif "gto" in problem.lower() or "geostationary transfer" in problem.lower():
            solution["analysis"].append("Target: Geostationary Transfer Orbit (GTO)")
            solution["recommendations"].append("GTO characteristics: Elliptical orbit, ~36,000 km apogee")
            solution["recommendations"].append("Advantages: Efficient path to geostationary orbit")
            solution["recommendations"].append("Disadvantages: Requires apogee kick motor for final insertion")
        
        elif "sso" in problem.lower() or "sun-synchronous" in problem.lower():
            solution["analysis"].append("Target: Sun-Synchronous Orbit (SSO)")
            solution["recommendations"].append("SSO characteristics: Polar orbit, maintains sun angle")
            solution["recommendations"].append("Advantages: Consistent lighting for Earth observation")
            solution["recommendations"].append("Disadvantages: Limited to specific inclinations")
        
        solution["reasoning"].append(
            "Orbital selection depends on mission requirements, energy budget, and operational needs"
        )
        
        return solution
    
    def _solve_propulsion_problem(self, problem: str, solution: Dict) -> Dict:
        """Solves propulsion and energy problems"""
        solution["analysis"].append("Analyzing propulsion system requirements")
        
        solution["recommendations"].append("ISRO Propulsion Systems:")
        solution["recommendations"].append("1. Vikas Engine (L110 stage) - Liquid propellant, 800kN thrust")
        solution["recommendations"].append("2. CE-20 Engine (C25 stage) - Cryogenic, 1900kN thrust")
        solution["recommendations"].append("3. S200 Booster - Solid propellant, 4800kN thrust")
        solution["recommendations"].append("4. Liquid Apogee Motor (LAM) - For orbital insertion")
        
        solution["solution"].append(
            "Propulsion system selection depends on mission delta-v requirements and payload mass"
        )
        
        solution["reasoning"].append(
            "Propulsion efficiency is critical for mission success - higher specific impulse enables greater payload capacity"
        )
        
        return solution
    
    def _solve_design_problem(self, problem: str, solution: Dict) -> Dict:
        """Solves design and configuration problems"""
        solution["analysis"].append("Analyzing design and configuration requirements")
        
        solution["recommendations"].append("Design Considerations:")
        solution["recommendations"].append("1. Structural integrity - withstand launch loads and vibration")
        solution["recommendations"].append("2. Thermal management - handle extreme temperature variations")
        solution["recommendations"].append("3. Power systems - solar panels or batteries for mission duration")
        solution["recommendations"].append("4. Communication systems - reliable ground station links")
        solution["recommendations"].append("5. Attitude control - maintain proper orientation")
        
        solution["solution"].append(
            "Integrated design approach ensures all subsystems work together efficiently"
        )
        
        solution["reasoning"].append(
            "Aerospace design requires balancing multiple constraints: mass, power, thermal, structural, and operational"
        )
        
        return solution
    
    def _solve_mission_planning_problem(self, problem: str, solution: Dict) -> Dict:
        """Solves mission planning problems"""
        solution["analysis"].append("Analyzing mission planning requirements")
        
        solution["recommendations"].append("Mission Planning Steps:")
        solution["recommendations"].append("1. Define mission objectives and success criteria")
        solution["recommendations"].append("2. Determine payload and orbital requirements")
        solution["recommendations"].append("3. Select appropriate launch vehicle")
        solution["recommendations"].append("4. Plan launch window and trajectory")
        solution["recommendations"].append("5. Develop contingency plans")
        solution["recommendations"].append("6. Coordinate with ground stations and tracking")
        
        solution["solution"].append(
            "Comprehensive mission planning ensures successful execution and risk mitigation"
        )
        
        solution["reasoning"].append(
            "Mission success depends on careful planning, coordination, and contingency preparation"
        )
        
        return solution
    
    def format_response_for_human(self, analysis: Dict) -> str:
        """
        Formats technical analysis into human-readable response
        
        Args:
            analysis: Technical analysis dictionary
        
        Returns:
            Formatted string for human understanding
        """
        response = []
        
        if analysis.get("problem_type"):
            response.append(f"**Problem Type**: {analysis['problem_type']}\n")
        
        if analysis.get("analysis"):
            response.append("**Analysis**:")
            for item in analysis["analysis"]:
                response.append(f"  • {item}")
            response.append("")
        
        if analysis.get("solution"):
            response.append("**Solution**:")
            for item in analysis["solution"]:
                response.append(f"  • {item}")
            response.append("")
        
        if analysis.get("recommendations"):
            response.append("**Recommendations**:")
            for item in analysis["recommendations"]:
                response.append(f"  • {item}")
            response.append("")
        
        if analysis.get("reasoning"):
            response.append("**Reasoning**:")
            for item in analysis["reasoning"]:
                response.append(f"  • {item}")
            response.append("")
        
        if analysis.get("constraints"):
            response.append("**Constraints**:")
            for item in analysis["constraints"]:
                response.append(f"  ⚠️  {item}")
            response.append("")
        
        if analysis.get("alternatives"):
            response.append("**Alternatives**:")
            for item in analysis["alternatives"]:
                response.append(f"  • {item}")
            response.append("")
        
        return "\n".join(response)
    
    def validate_aerospace_logic(self, claim: str, context: List[str] = None) -> Tuple[bool, str]:
        """
        Validates if an aerospace claim is logically correct
        
        Args:
            claim: Aerospace claim to validate
            context: Optional context from RAG system
        
        Returns:
            Tuple of (is_valid, explanation)
        """
        claim_lower = claim.lower()
        
        # Check for logical contradictions
        contradictions = [
            (r"pslv.*gto.*capacity.*2500", "PSLV cannot reach GTO with 2500kg - max is ~1600kg to LEO"),
            (r"pslv.*gto", "PSLV is not designed for GTO missions - use GSLV instead"),
            (r"gslv.*leo.*capacity.*1000", "GSLV Mk III can carry much more than 1000kg to LEO"),
            (r"chandrayaan.*nuclear", "Chandrayaan missions use chemical propulsion, not nuclear"),
            (r"satellite.*negative.*mass", "Satellites cannot have negative mass"),
            (r"orbit.*below.*earth.*surface", "Orbits cannot be below Earth's surface"),
        ]
        
        for pattern, explanation in contradictions:
            if re.search(pattern, claim_lower):
                return False, explanation
        
        # Check for logical consistency
        if "payload" in claim_lower and "mass" in claim_lower:
            mass_match = re.search(r'(\d+)\s*kg', claim)
            if mass_match:
                mass = int(mass_match.group(1))
                if mass < 0:
                    return False, "Payload mass cannot be negative"
                if mass > 50000:
                    return False, "Payload mass exceeds typical satellite mass range"
        
        return True, "Claim is logically consistent with aerospace principles"

# Singleton instance
aerospace_helper = AerospaceHelper()
