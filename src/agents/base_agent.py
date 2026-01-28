"""
Base Agent Class
All agents (Auditor, Fixer, Judge) inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    Provides common functionality and enforces the agent interface.
    """
    
    def __init__(self, name: str):
        """
        Initialize the base agent.
        
        Args:
            name: Name of the agent (e.g., "AuditorAgent")
        """
        self.name = name
        print(f"✨ {name} created")
    
    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's task.
        
        This method must be implemented by all agent subclasses.
        
        Args:
            state: Current workflow state dictionary
        
        Returns:
            Dictionary with updates to merge into state
        """
        pass
    
    def _create_error_result(self, state: Dict[str, Any], error: str) -> Dict[str, Any]:
        """
        Create a standardized error result.
        
        Args:
            state: Current state
            error: Error message
        
        Returns:
            State updates with error information
        """
        return {
            "agent_outputs": {
                **(state.get("agent_outputs") or {}),
                f"{self.name}_error": error
            },
            "errors": [
                *(state.get("errors") or []),
                f"{self.name}: {error}"
            ]
        }
    
    def _log(self, message: str):
        """
        Print a log message with agent name prefix.
        
        Args:
            message: Message to log
        """
        print(f"[{self.name}] {message}")