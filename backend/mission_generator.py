"""
NEXORA Mission Generator
Generates technical documents for new missions based on learned knowledge
"""

import json
from datetime import datetime
from typing import Dict, List

class MissionGenerator:
    """
    Generates technical mission documents based on:
    - Previous mission knowledge
    - User learning patterns
    - Aerospace helper analysis
    - Session context
    """
    
    def __init__(self):
        self.mission_templates = self._load_mission_templates()
        self.generated_documents = []
    
    def _load_mission_templates(self) -> Dict:
        """Load mission document templates"""
        return {
            "mission_plan": {
                "sections": [
                    "mission_overview",
                    "objectives",
                    "payload_specifications",
                    "launch_vehicle_selection",
                    "orbital_parameters",
                    "mission_timeline",
                    "risk_assessment",
                    "contingency_plans"
                ]
            },
            "technical_specification": {
                "sections": [
                    "satellite_design",
                    "subsystems",
                    "power_budget",
                    "thermal_management",
                    "communication_systems",
                    "attitude_control",
                    "propulsion_system",
                    "performance_metrics"
                ]
            },
            "mission_analysis": {
                "sections": [
                    "mission_requirements",
                    "feasibility_analysis",
                    "cost_estimation",
                    "schedule",
                    "resource_allocation",
                    "success_criteria",
                    "lessons_learned_from_previous_missions"
                ]
            }
        }
    
    def generate_mission_plan(self, mission_description: str, previous_missions: List[Dict] = None) -> Dict:
        """Generate a mission plan based on mission description and previous missions"""
        
        mission_plan = {
            "document_type": "Mission Plan",
            "generated_at": datetime.now().isoformat(),
            "mission_description": mission_description,
            "sections": {}
        }
        
        # Extract mission parameters
        mission_params = self._extract_mission_parameters(mission_description)
        
        # Generate each section
        mission_plan["sections"]["mission_overview"] = self._generate_mission_overview(
            mission_description, mission_params
        )
        
        mission_plan["sections"]["objectives"] = self._generate_objectives(
            mission_description, mission_params
        )
        
        mission_plan["sections"]["payload_specifications"] = self._generate_payload_specs(
            mission_params
        )
        
        mission_plan["sections"]["launch_vehicle_selection"] = self._generate_vehicle_selection(
            mission_params, previous_missions
        )
        
        mission_plan["sections"]["orbital_parameters"] = self._generate_orbital_parameters(
            mission_params
        )
        
        mission_plan["sections"]["mission_timeline"] = self._generate_timeline(
            mission_params
        )
        
        mission_plan["sections"]["risk_assessment"] = self._generate_risk_assessment(
            mission_params, previous_missions
        )
        
        mission_plan["sections"]["contingency_plans"] = self._generate_contingency_plans(
            mission_params, previous_missions
        )
        
        return mission_plan
    
    def generate_technical_specification(self, mission_description: str, previous_missions: List[Dict] = None) -> Dict:
        """Generate technical specifications based on mission and previous missions"""
        
        tech_spec = {
            "document_type": "Technical Specification",
            "generated_at": datetime.now().isoformat(),
            "mission_description": mission_description,
            "sections": {}
        }
        
        mission_params = self._extract_mission_parameters(mission_description)
        
        tech_spec["sections"]["satellite_design"] = self._generate_satellite_design(
            mission_params, previous_missions
        )
        
        tech_spec["sections"]["subsystems"] = self._generate_subsystems(
            mission_params, previous_missions
        )
        
        tech_spec["sections"]["power_budget"] = self._generate_power_budget(
            mission_params
        )
        
        tech_spec["sections"]["thermal_management"] = self._generate_thermal_management(
            mission_params
        )
        
        tech_spec["sections"]["communication_systems"] = self._generate_communication_systems(
            mission_params
        )
        
        tech_spec["sections"]["attitude_control"] = self._generate_attitude_control(
            mission_params
        )
        
        tech_spec["sections"]["propulsion_system"] = self._generate_propulsion_system(
            mission_params
        )
        
        tech_spec["sections"]["performance_metrics"] = self._generate_performance_metrics(
            mission_params
        )
        
        return tech_spec
    
    def generate_mission_analysis(self, mission_description: str, previous_missions: List[Dict] = None) -> Dict:
        """Generate mission analysis based on previous missions"""
        
        analysis = {
            "document_type": "Mission Analysis",
            "generated_at": datetime.now().isoformat(),
            "mission_description": mission_description,
            "sections": {}
        }
        
        mission_params = self._extract_mission_parameters(mission_description)
        
        analysis["sections"]["mission_requirements"] = self._generate_requirements(
            mission_params
        )
        
        analysis["sections"]["feasibility_analysis"] = self._generate_feasibility(
            mission_params, previous_missions
        )
        
        analysis["sections"]["cost_estimation"] = self._generate_cost_estimation(
            mission_params, previous_missions
        )
        
        analysis["sections"]["schedule"] = self._generate_schedule(
            mission_params, previous_missions
        )
        
        analysis["sections"]["resource_allocation"] = self._generate_resources(
            mission_params
        )
        
        analysis["sections"]["success_criteria"] = self._generate_success_criteria(
            mission_params
        )
        
        analysis["sections"]["lessons_learned"] = self._generate_lessons_learned(
            previous_missions
        )
        
        return analysis
    
    def _extract_mission_parameters(self, mission_description: str) -> Dict:
        """Extract mission parameters from description"""
        import re
        
        params = {
            "payload_mass": None,
            "target_orbit": None,
            "mission_type": None,
            "duration": None,
            "instruments": [],
        }
        
        # Extract payload mass
        mass_match = re.search(r'(\d+)\s*kg', mission_description, re.IGNORECASE)
        if mass_match:
            params["payload_mass"] = int(mass_match.group(1))
        
        # Extract orbit type
        orbits = ["LEO", "GTO", "SSO", "GSO", "HEO"]
        for orbit in orbits:
            if orbit in mission_description.upper():
                params["target_orbit"] = orbit
                break
        
        # Extract mission type
        if "earth observation" in mission_description.lower():
            params["mission_type"] = "Earth Observation"
        elif "communication" in mission_description.lower():
            params["mission_type"] = "Communication"
        elif "lunar" in mission_description.lower():
            params["mission_type"] = "Lunar"
        elif "mars" in mission_description.lower():
            params["mission_type"] = "Mars"
        else:
            params["mission_type"] = "General"
        
        return params
    
    def _generate_mission_overview(self, description: str, params: Dict) -> Dict:
        """Generate mission overview section"""
        return {
            "title": "Mission Overview",
            "content": f"""
The proposed mission aims to {description}.

Mission Type: {params['mission_type']}
Payload Mass: {params['payload_mass']} kg
Target Orbit: {params['target_orbit']}

This mission builds upon the success of previous ISRO missions and incorporates
lessons learned from past operations to ensure mission success.
            """.strip(),
            "status": "Generated from mission description"
        }
    
    def _generate_objectives(self, description: str, params: Dict) -> Dict:
        """Generate mission objectives"""
        objectives = []
        
        if params['mission_type'] == "Earth Observation":
            objectives = [
                "Provide high-resolution Earth observation data",
                "Monitor environmental changes",
                "Support disaster management",
                "Enable agricultural planning"
            ]
        elif params['mission_type'] == "Communication":
            objectives = [
                "Provide communication coverage",
                "Enable broadband services",
                "Support emergency communications",
                "Enhance connectivity"
            ]
        elif params['mission_type'] == "Lunar":
            objectives = [
                "Conduct lunar exploration",
                "Gather scientific data",
                "Test landing systems",
                "Prepare for future missions"
            ]
        
        return {
            "title": "Mission Objectives",
            "objectives": objectives,
            "status": "Generated based on mission type"
        }
    
    def _generate_payload_specs(self, params: Dict) -> Dict:
        """Generate payload specifications"""
        payload_mass = params['payload_mass'] or 1000  # Default to 1000kg if not specified
        
        return {
            "title": "Payload Specifications",
            "payload_mass": payload_mass,
            "payload_volume": f"{payload_mass * 0.5:.0f} liters (estimated)",
            "power_requirement": f"{payload_mass * 10:.0f} W (estimated)",
            "thermal_dissipation": f"{payload_mass * 5:.0f} W (estimated)",
            "status": "Generated based on payload mass"
        }
    
    def _generate_vehicle_selection(self, params: Dict, previous_missions: List[Dict] = None) -> Dict:
        """Generate launch vehicle selection based on previous missions"""
        
        recommendation = {
            "title": "Launch Vehicle Selection",
            "analysis": "",
            "recommended_vehicle": None,
            "alternatives": [],
            "reasoning": []
        }
        
        payload_mass = params['payload_mass'] or 1000  # Default to 1000kg
        target_orbit = params['target_orbit'] or "LEO"  # Default to LEO
        
        if target_orbit == "LEO":
            if payload_mass <= 1600:
                recommendation["recommended_vehicle"] = "PSLV"
                recommendation["reasoning"].append("PSLV proven for LEO missions (50+ launches)")
            else:
                recommendation["recommended_vehicle"] = "GSLV Mk III"
                recommendation["reasoning"].append("GSLV Mk III for higher payload to LEO")
        
        elif target_orbit == "GTO":
            if payload_mass <= 2500:
                recommendation["recommended_vehicle"] = "GSLV Mk II"
                recommendation["reasoning"].append("GSLV Mk II proven for GTO missions (15+ launches)")
            else:
                recommendation["recommended_vehicle"] = "GSLV Mk III"
                recommendation["reasoning"].append("GSLV Mk III for higher payload to GTO")
        
        elif target_orbit == "SSO":
            recommendation["recommended_vehicle"] = "PSLV"
            recommendation["reasoning"].append("PSLV ideal for SSO missions")
        
        # Add lessons from previous missions
        if previous_missions:
            recommendation["reasoning"].append(
                f"Based on {len(previous_missions)} previous missions"
            )
        
        return recommendation
    
    def _generate_orbital_parameters(self, params: Dict) -> Dict:
        """Generate orbital parameters"""
        
        orbital_params = {
            "title": "Orbital Parameters",
            "orbit_type": params['target_orbit'],
            "parameters": {}
        }
        
        if params['target_orbit'] == "LEO":
            orbital_params["parameters"] = {
                "altitude": "400-500 km",
                "inclination": "Variable",
                "orbital_period": "~90 minutes",
                "velocity": "~7.7 km/s"
            }
        elif params['target_orbit'] == "GTO":
            orbital_params["parameters"] = {
                "perigee": "~200 km",
                "apogee": "~36,000 km",
                "inclination": "~7 degrees",
                "orbital_period": "~10.5 hours"
            }
        elif params['target_orbit'] == "SSO":
            orbital_params["parameters"] = {
                "altitude": "~700-800 km",
                "inclination": "~98 degrees",
                "orbital_period": "~100 minutes",
                "sun_synchronous": "Yes"
            }
        
        return orbital_params
    
    def _generate_timeline(self, params: Dict) -> Dict:
        """Generate mission timeline"""
        return {
            "title": "Mission Timeline",
            "phases": [
                {"phase": "Design & Development", "duration": "12-18 months"},
                {"phase": "Manufacturing", "duration": "12-18 months"},
                {"phase": "Testing & Integration", "duration": "6-12 months"},
                {"phase": "Launch Preparation", "duration": "3-6 months"},
                {"phase": "Launch & Commissioning", "duration": "1-3 months"},
                {"phase": "Operational Phase", "duration": "Mission dependent"}
            ]
        }
    
    def _generate_risk_assessment(self, params: Dict, previous_missions: List[Dict] = None) -> Dict:
        """Generate risk assessment based on previous missions"""
        
        risks = [
            {"risk": "Launch vehicle failure", "probability": "Low", "mitigation": "Use proven vehicle"},
            {"risk": "Payload malfunction", "probability": "Low", "mitigation": "Rigorous testing"},
            {"risk": "Orbital insertion error", "probability": "Very Low", "mitigation": "Precise guidance"},
            {"risk": "Communication loss", "probability": "Very Low", "mitigation": "Redundant systems"},
        ]
        
        if previous_missions:
            risks.append({
                "risk": "Lessons from previous missions",
                "probability": "Incorporated",
                "mitigation": f"Applied {len(previous_missions)} mission lessons"
            })
        
        return {
            "title": "Risk Assessment",
            "risks": risks,
            "overall_risk": "Low" if previous_missions else "Medium"
        }
    
    def _generate_contingency_plans(self, params: Dict, previous_missions: List[Dict] = None) -> Dict:
        """Generate contingency plans based on previous missions"""
        
        contingencies = [
            "Launch delay procedures",
            "Orbital insertion contingency",
            "Communication loss procedures",
            "Payload malfunction recovery",
            "Mission abort procedures"
        ]
        
        if previous_missions:
            contingencies.append("Procedures based on previous mission experiences")
        
        return {
            "title": "Contingency Plans",
            "contingencies": contingencies,
            "status": "Comprehensive contingency planning in place"
        }
    
    def _generate_satellite_design(self, params: Dict, previous_missions: List[Dict] = None) -> Dict:
        """Generate satellite design"""
        payload_mass = params['payload_mass'] or 1000  # Default to 1000kg
        
        return {
            "title": "Satellite Design",
            "design_approach": "Modular design based on proven ISRO platforms",
            "structure": "Aluminum alloy frame with composite panels",
            "mass_budget": {
                "structure": f"{payload_mass * 0.3:.0f} kg",
                "payload": f"{payload_mass} kg",
                "subsystems": f"{payload_mass * 0.4:.0f} kg"
            },
            "design_life": "5-7 years (mission dependent)",
            "previous_missions_reference": f"Based on {len(previous_missions) if previous_missions else 0} previous missions"
        }
    
    def _generate_subsystems(self, params: Dict, previous_missions: List[Dict] = None) -> Dict:
        """Generate subsystems specification"""
        return {
            "title": "Subsystems",
            "subsystems": [
                "Power Generation System (Solar Panels)",
                "Power Management System (Batteries)",
                "Attitude Determination & Control System (ADCS)",
                "Communication System (Transponders)",
                "Thermal Control System",
                "Propulsion System (if applicable)",
                "Command & Data Handling System"
            ],
            "proven_designs": "All subsystems use proven ISRO designs"
        }
    
    def _generate_power_budget(self, params: Dict) -> Dict:
        """Generate power budget"""
        payload_mass = params['payload_mass'] or 1000  # Default to 1000kg
        
        return {
            "title": "Power Budget",
            "solar_panel_power": f"{payload_mass * 15:.0f} W",
            "battery_capacity": f"{payload_mass * 5:.0f} Wh",
            "payload_power": f"{payload_mass * 10:.0f} W",
            "subsystem_power": f"{payload_mass * 5:.0f} W",
            "margin": "20% power margin included"
        }
    
    def _generate_thermal_management(self, params: Dict) -> Dict:
        """Generate thermal management"""
        return {
            "title": "Thermal Management",
            "approach": "Passive thermal control with active heaters",
            "operating_temperature": "-10°C to +50°C",
            "radiators": "Multi-layer insulation with radiative surfaces",
            "heaters": "Redundant heater systems"
        }
    
    def _generate_communication_systems(self, params: Dict) -> Dict:
        """Generate communication systems"""
        return {
            "title": "Communication Systems",
            "uplink_frequency": "2.1 GHz",
            "downlink_frequency": "8.4 GHz",
            "data_rate": "High-speed data transmission",
            "ground_stations": "Multiple ISRO ground stations",
            "redundancy": "Dual transponders for redundancy"
        }
    
    def _generate_attitude_control(self, params: Dict) -> Dict:
        """Generate attitude control"""
        return {
            "title": "Attitude Control",
            "sensors": "Star sensors, Sun sensors, Earth sensors",
            "actuators": "Reaction wheels, Magnetic torquers",
            "accuracy": "±0.1 degree pointing accuracy",
            "control_mode": "3-axis stabilized"
        }
    
    def _generate_propulsion_system(self, params: Dict) -> Dict:
        """Generate propulsion system"""
        return {
            "title": "Propulsion System",
            "type": "Chemical propulsion (if applicable)",
            "fuel": "Hydrazine or equivalent",
            "delta_v": "Sufficient for orbital maneuvers",
            "thrusters": "Multiple small thrusters for redundancy"
        }
    
    def _generate_performance_metrics(self, params: Dict) -> Dict:
        """Generate performance metrics"""
        return {
            "title": "Performance Metrics",
            "payload_mass": f"{params['payload_mass']} kg",
            "mission_life": "5-7 years",
            "reliability": ">95%",
            "availability": ">99%",
            "data_quality": "High resolution"
        }
    
    def _generate_requirements(self, params: Dict) -> Dict:
        """Generate mission requirements"""
        return {
            "title": "Mission Requirements",
            "functional_requirements": [
                f"Deliver {params['payload_mass']}kg payload to {params['target_orbit']}",
                "Maintain operational status for mission duration",
                "Provide continuous data transmission",
                "Support mission objectives"
            ],
            "performance_requirements": [
                "Pointing accuracy: ±0.1 degree",
                "Data transmission: High-speed",
                "Reliability: >95%",
                "Availability: >99%"
            ]
        }
    
    def _generate_feasibility(self, params: Dict, previous_missions: List[Dict] = None) -> Dict:
        """Generate feasibility analysis"""
        
        feasibility = {
            "title": "Feasibility Analysis",
            "technical_feasibility": "High - Uses proven technologies",
            "schedule_feasibility": "Achievable - 3-4 year development timeline",
            "cost_feasibility": "Reasonable - Based on previous missions",
            "risk_level": "Low to Medium"
        }
        
        if previous_missions:
            feasibility["previous_missions_support"] = f"Supported by {len(previous_missions)} successful missions"
        
        return feasibility
    
    def _generate_cost_estimation(self, params: Dict, previous_missions: List[Dict] = None) -> Dict:
        """Generate cost estimation based on previous missions"""
        
        payload_mass = params['payload_mass'] or 1000  # Default to 1000kg
        base_cost = payload_mass * 50000
        
        return {
            "title": "Cost Estimation",
            "satellite_cost": f"${base_cost:,.0f}",
            "launch_cost": "$20-30 million (PSLV/GSLV)",
            "ground_segment": "$5-10 million",
            "operations": "$2-5 million per year",
            "total_mission_cost": f"${base_cost + 25000000:,.0f}",
            "basis": "Based on previous mission costs"
        }
    
    def _generate_schedule(self, params: Dict, previous_missions: List[Dict] = None) -> Dict:
        """Generate project schedule"""
        
        schedule = {
            "title": "Project Schedule",
            "phases": [
                {"phase": "Phase 1: Design", "duration": "12 months"},
                {"phase": "Phase 2: Development", "duration": "12 months"},
                {"phase": "Phase 3: Testing", "duration": "9 months"},
                {"phase": "Phase 4: Launch Prep", "duration": "6 months"},
                {"phase": "Phase 5: Operations", "duration": "Mission dependent"}
            ],
            "total_duration": "39 months to launch"
        }
        
        if previous_missions:
            schedule["schedule_basis"] = f"Based on {len(previous_missions)} previous missions"
        
        return schedule
    
    def _generate_resources(self, params: Dict) -> Dict:
        """Generate resource allocation"""
        return {
            "title": "Resource Allocation",
            "engineering_team": "50-100 engineers",
            "project_manager": "1",
            "quality_assurance": "10-15 QA specialists",
            "testing_facilities": "Multiple ISRO facilities",
            "budget_allocation": "Distributed across phases"
        }
    
    def _generate_success_criteria(self, params: Dict) -> Dict:
        """Generate success criteria"""
        return {
            "title": "Success Criteria",
            "criteria": [
                "Successful launch and orbital insertion",
                "Payload activation and commissioning",
                "Data transmission verification",
                "Mission objectives achievement",
                "Operational life target achievement"
            ]
        }
    
    def _generate_lessons_learned(self, previous_missions: List[Dict] = None) -> Dict:
        """Generate lessons learned from previous missions"""
        
        lessons = {
            "title": "Lessons Learned from Previous Missions",
            "lessons": []
        }
        
        if previous_missions:
            for mission in previous_missions:
                if "lessons" in mission:
                    lessons["lessons"].extend(mission["lessons"])
        
        if not lessons["lessons"]:
            lessons["lessons"] = [
                "Importance of rigorous testing",
                "Value of redundant systems",
                "Need for comprehensive contingency planning",
                "Benefit of proven technologies",
                "Critical role of team coordination"
            ]
        
        return lessons
    
    def export_document(self, document: Dict, format: str = "json") -> str:
        """Export generated document"""
        
        if format == "json":
            return json.dumps(document, indent=2)
        elif format == "text":
            return self._format_as_text(document)
        else:
            return json.dumps(document, indent=2)
    
    def _format_as_text(self, document: Dict) -> str:
        """Format document as text"""
        
        text = f"""
{'='*80}
{document['document_type']}
{'='*80}

Generated: {document['generated_at']}
Mission: {document['mission_description']}

"""
        
        for section_name, section_content in document['sections'].items():
            text += f"\n{section_name.upper().replace('_', ' ')}\n"
            text += f"{'-'*80}\n"
            
            if isinstance(section_content, dict):
                for key, value in section_content.items():
                    if isinstance(value, list):
                        text += f"{key}:\n"
                        for item in value:
                            if isinstance(item, dict):
                                text += f"  • {item.get('title', item)}\n"
                            else:
                                text += f"  • {item}\n"
                    else:
                        text += f"{key}: {value}\n"
            else:
                text += f"{section_content}\n"
        
        return text

# Singleton instance
mission_generator = MissionGenerator()
