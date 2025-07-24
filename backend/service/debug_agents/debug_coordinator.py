"""
Debug Coordinator Agent - orchestrates the debugging process
"""
from typing import Dict, Any, List
from agents.agent import Agent

from .base_agent import BaseDebugAgent
from ..tools.validation_tools import run_workflow, analyze_error_type, save_current_workflow


class DebugCoordinator(BaseDebugAgent):
    """Debug coordinator agent that orchestrates the debugging process"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.session_id = config.get("session_id", "")
    
    def _create_agent(self) -> Agent:
        """Create the debug coordinator agent"""
        return Agent(
            name=self.name,
            instructions=self.config.get("instructions", ""),
            model=self.model,
            tools=self.get_tools(),
        )
    
    def get_tools(self) -> List:
        """Get tools for debug coordinator"""
        return [run_workflow, analyze_error_type, save_current_workflow] 