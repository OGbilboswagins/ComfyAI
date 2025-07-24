"""
Parameter Agent - handles parameter-related errors and fixes
"""
from typing import Dict, Any, List
from agents.agent import Agent

from .base_agent import BaseDebugAgent
from ..tools.parameter_tools import (
    get_node_parameters, find_matching_parameter_value, 
    get_model_files, suggest_model_download, update_workflow_parameter
)


class ParameterAgent(BaseDebugAgent):
    """Parameter agent for handling parameter-related issues"""
    
    def _create_agent(self) -> Agent:
        """Create the parameter agent"""
        return Agent(
            name=self.name,
            model=self.model,
            handoff_description=self.config.get("handoff_description", ""),
            instructions=self.config.get("instructions", ""),
            tools=self.get_tools(),
            handoffs=self.get_handoffs()
        )
    
    def get_tools(self) -> List:
        """Get tools for parameter agent"""
        return [
            get_node_parameters, find_matching_parameter_value, 
            get_model_files, suggest_model_download, update_workflow_parameter
        ] 