"""
Base Agent class for ComfyUI debugging agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from agents.agent import Agent


class BaseDebugAgent(ABC):
    """Base class for all debug agents"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", "UnknownAgent")
        self.model = config.get("model", "us.anthropic.claude-sonnet-4-20250514-v1:0")
        self._agent: Optional[Agent] = None
    
    @property
    def agent(self) -> Agent:
        """Get the underlying Agent instance"""
        if self._agent is None:
            self._agent = self._create_agent()
        return self._agent
    
    @abstractmethod
    def _create_agent(self) -> Agent:
        """Create and configure the Agent instance"""
        pass
    
    @abstractmethod
    def get_tools(self) -> List:
        """Get the tools this agent uses"""
        pass
    
    def get_handoffs(self) -> List[Agent]:
        """Get the agents this agent can hand off to"""
        return []
    
    def set_handoffs(self, handoff_agents: List[Agent]):
        """Set the handoff agents"""
        if self._agent:
            self._agent.handoffs = handoff_agents 