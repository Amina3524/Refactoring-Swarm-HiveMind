"""
Runner pour pylint (analyse de qualité de code).
"""

import subprocess
import os
from typing import Dict, Any

def run_pylint(filepath: str) -> Dict[str, Any]:
    """
    Exécute pylint sur un fichier.
    
    Retourne:
    - status: "OK" ou "FAILED"
    - score: score pylint 0-10
    - issues: nombre de problèmes
    """
    
    if not os.path.exists(filepath):
        return {
            "status": "FAILED",
            "score": 0,
            "issues": 1
        }
    
    try:
        result = subprocess.run(
            ["pylint", filepath, "--exit-zero"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Parser le score (dernière ligne)
        lines = result.stdout.split('\n')
        score = 10.0
        
        for line in lines:
            if 'rated at' in line:
                try:
                    score = float(line.split('rated at ')[1].split('/')[0])
                except:
                    pass
        
        return {
            "status": "OK",
            "score": score,
            "issues": max(0, int(10 - score))
        }
    
    except Exception as e:
        return {
            "status": "FAILED",
            "score": 0,
            "issues": 1,
            "error": str(e)
        }


def get_pylint_score(filepath: str) -> float:
    """Récupère juste le score."""
    result = run_pylint(filepath)
    return result.get('score', 0)