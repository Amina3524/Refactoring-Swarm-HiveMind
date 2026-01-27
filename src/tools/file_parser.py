"""
Parser simple de fichiers Python pour tests.
"""

import os
import ast
from typing import Dict, Any

def parse_python_file(filepath: str) -> Dict[str, Any]:
    """
    Parse un fichier Python simple.
    
    Retourne:
    - lines: nombre de lignes
    - syntax_valid: True si pas d'erreur syntaxe
    - syntax_errors: liste des erreurs
    - functions: nombre de fonctions
    - missing_docstrings: nombre sans docstring
    """
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Fichier {filepath} introuvable")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    result = {
        "lines": len(content.splitlines()),
        "syntax_valid": True,
        "syntax_errors": [],
        "functions": 0,
        "missing_docstrings": 0
    }
    
    # Vérifier syntaxe
    try:
        tree = ast.parse(content)
        
        # Compter fonctions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                result["functions"] += 1
                if not ast.get_docstring(node):
                    result["missing_docstrings"] += 1
    
    except SyntaxError as e:
        result["syntax_valid"] = False
        result["syntax_errors"].append(str(e))
    
    return result