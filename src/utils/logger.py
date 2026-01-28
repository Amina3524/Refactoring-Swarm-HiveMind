"""
Experiment Logger
This module is critical for the scientific study aspect of the TP.
ALL LLM interactions MUST be logged using this module.
"""

import json
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any


class ActionType(Enum):
    """
    Standardized action types (DO NOT MODIFY)
    These are required by the TP specification.
    """
    ANALYSIS = "ANALYSIS"  # Agent reads code to understand/check
    GENERATION = "GENERATION"  # Agent creates new content (tests, docs)
    DEBUG = "DEBUG"  # Agent analyzes errors/stacktraces
    FIX = "FIX"  # Agent rewrites code to correct bugs


class ExperimentLogger:
    """
    Singleton logger for experiment data.
    Ensures thread-safe logging to experiment_data.json
    """
    
    _instance = None
    _log_file = Path("logs/experiment_data.json")
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the log file."""
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create empty log file if it doesn't exist
        if not self._log_file.exists():
            self._write_logs([])
    
    def _read_logs(self) -> list:
        """Read existing logs."""
        try:
            with open(self._log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _write_logs(self, logs: list):
        """Write logs to file."""
        with open(self._log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    
    def log(self, entry: Dict[str, Any]):
        """Add a log entry."""
        logs = self._read_logs()
        logs.append(entry)
        self._write_logs(logs)


# Singleton instance
_logger = ExperimentLogger()


def log_experiment(
    agent_name: str,
    model_used: str,
    action: ActionType,
    details: Dict[str, Any],
    status: str = "SUCCESS"
):
    """
    Log an experiment action.
    
    CRITICAL: This function MUST be called after every LLM interaction!
    
    Args:
        agent_name: Name of the agent (e.g., "Auditor_Agent")
        model_used: LLM model name (e.g., "gemini-2.0-flash-exp")
        action: ActionType enum value (ANALYSIS, GENERATION, DEBUG, or FIX)
        details: Dictionary containing:
            - input_prompt: REQUIRED - Exact text sent to LLM
            - output_response: REQUIRED - Raw response from LLM
            - Additional context-specific fields
        status: "SUCCESS", "FAILURE", or "INFO"
    
    Raises:
        ValueError: If input_prompt or output_response is missing
    """
    
    # Validate required fields
    if "input_prompt" not in details:
        raise ValueError("details must contain 'input_prompt' field")
    if "output_response" not in details:
        raise ValueError("details must contain 'output_response' field")
    
    # Validate action type
    if not isinstance(action, ActionType):
        raise ValueError(f"action must be an ActionType enum, got {type(action)}")
    
    # Create log entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent_name": agent_name,
        "model_used": model_used,
        "action": action.value,  # Convert enum to string
        "status": status,
        "details": details
    }
    
    # Log it
    _logger.log(entry)
    
    # Print confirmation
    print(f"📝 Logged: {agent_name} - {action.value} - {status}")


def get_log_summary() -> Dict[str, Any]:
    """
    Get a summary of logged experiments.
    
    Returns:
        Dictionary with statistics about logged actions
    """
    logs = _logger._read_logs()
    
    if not logs:
        return {"total": 0}
    
    summary = {
        "total": len(logs),
        "by_agent": {},
        "by_action": {},
        "by_status": {}
    }
    
    for entry in logs:
        # Count by agent
        agent = entry.get("agent_name", "unknown")
        summary["by_agent"][agent] = summary["by_agent"].get(agent, 0) + 1
        
        # Count by action
        action = entry.get("action", "unknown")
        summary["by_action"][action] = summary["by_action"].get(action, 0) + 1
        
        # Count by status
        status = entry.get("status", "unknown")
        summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
    
    return summary


def clear_logs():
    """Clear all experiment logs. Use with caution!"""
    _logger._write_logs([])
    print("🧹 Cleared all experiment logs")