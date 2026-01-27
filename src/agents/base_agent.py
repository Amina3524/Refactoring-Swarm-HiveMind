# src/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, name: str, tools: Dict = None, prompts: Dict = None):
        self.name = name
        self.tools = tools or {}
        self.prompts = prompts or {}
    
    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's task"""
        pass
    
    def log_action(self, action_type: str, details: Dict):
        """Helper method for logging"""
        from src.utils.logger import log_experiment, ActionType
        
        action_map = {
            "analyze": ActionType.ANALYSIS,
            "fix": ActionType.FIX,
            "test": ActionType.DEBUG,
            "generate": ActionType.GENERATION
        }
        
        log_experiment(
            agent_name=self.name,
            model_used="gemini-2.0-flash",
            action=action_map.get(action_type, ActionType.ANALYSIS),
            details=details,
            status="SUCCESS"
        )