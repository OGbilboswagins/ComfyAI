"""
Workflow Rewrite Agent - handles structural workflow fixes
"""
from typing import Dict, Any, List
from agents.agent import Agent

from .base_agent import BaseDebugAgent
from ..tools.workflow_tools import (
    get_current_workflow, get_node_info, update_workflow,
    validate_workflow_connections, fix_node_connections, 
    add_missing_node, remove_node
)


class WorkflowRewriteAgent(BaseDebugAgent):
    """Workflow rewrite agent for handling structural issues"""
    
    def _create_agent(self) -> Agent:
        """Create the workflow rewrite agent"""
        return Agent(
            name=self.name,
            model=self.model,
            handoff_description=self.config.get("handoff_description", ""),
            instructions=self.config.get("instructions", ""),
            tools=self.get_tools(),
            handoffs=self.get_handoffs()
        )
    
    def get_tools(self) -> List:
        """Get tools for workflow rewrite agent"""
        return [
            get_current_workflow, get_node_info, update_workflow,
            validate_workflow_connections, fix_node_connections, 
            add_missing_node, remove_node
        ] 