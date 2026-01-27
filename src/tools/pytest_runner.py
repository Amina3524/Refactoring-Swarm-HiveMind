"""
Runner pour exécuter des tests avec pytest.
"""

import subprocess
import os
from typing import Dict, Any

def run_tests(test_file: str) -> Dict[str, Any]:
    """
    Exécute les tests avec pytest.
    
    Retourne:
    - all_passed: True si tous les tests passent
    - passed: nombre de tests réussis
    - failed: nombre de tests échoués
    """
    
    if not os.path.exists(test_file):
        return {
            "all_passed": False,
            "passed": 0,
            "failed": 1
        }
    
    try:
        result = subprocess.run(
            ["pytest", test_file, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parser le résultat
        output = result.stdout + result.stderr
        
        passed = 0
        failed = 0
        
        for line in output.split('\n'):
            if 'passed' in line:
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'passed':
                            passed = int(parts[i-1])
                except:
                    pass
            if 'failed' in line:
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'failed':
                            failed = int(parts[i-1])
                except:
                    pass
        
        return {
            "all_passed": failed == 0,
            "passed": passed,
            "failed": failed
        }
    
    except Exception as e:
        return {
            "all_passed": False,
            "passed": 0,
            "failed": 1,
            "error": str(e)
        }
    