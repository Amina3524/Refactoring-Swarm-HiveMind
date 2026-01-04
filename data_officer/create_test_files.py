"""
SANDBOX MANAGER - Data Officer
Crée la structure complète pour tester le système.
"""

import os
import json
from datetime import datetime

def create_sandbox_structure(base_dir: str = "sandbox") -> dict:
    """
    Crée toute la structure sandbox avec fichiers de test.
    Retourne un rapport des fichiers créés.
    """
    
    print("📁 CRÉATION DU SANDBOX COMPLET")
    print("=" * 60)
    
    # 1. Créer les dossiers
    directories = [
        base_dir,
        f"{base_dir}/test_files",
        f"{base_dir}/test_dataset",
        f"{base_dir}/buggy_code",
        f"{base_dir}/clean_code",
        f"{base_dir}/hidden_tests"  # Pour simuler le "hidden dataset"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Dossier créé: {directory}")
    
    # 2. Métadonnées des fichiers (pour validation)
    metadata = {
        "creation_date": datetime.now().isoformat(),
        "purpose": "Dataset de test pour The Refactoring Swarm",
        "files": {}
    }
    
    # 3. Créer les fichiers buggés (DIVISION PAR ZÉRO)
    buggy_files = {
        # Fichier 1: Division par zéro + mauvais nommage
        f"{base_dir}/test_files/buggy_1.py": {
            "content": '''# Fichier buggé - Division par zéro
def calculate_average(numbers):
    # BUG: Division par zéro possible
    return sum(numbers) / len(numbers)

def bad_naming(x):
    y = x * 2  # Mauvais nom de variable
    return y

# Pas de tests unitaires
print("Test buggy_1")
print(calculate_average([]))  # Va planter''',
            "expected_issues": ["ZeroDivisionError", "bad_variable_name", "no_tests"],
            "difficulty": "easy"
        },
        
        # Fichier 2: Problèmes de style PEP8
        f"{base_dir}/test_files/buggy_2.py": {
            "content": '''# Problèmes de style PEP8
import os,sys  # Import sur une ligne - VIOLATION PEP8

class BadClass:
    def __init__(self):
        self.a=1  # Pas d'espaces - VIOLATION
        self.b=2
    
    def m(self):  # Pas de docstring - VIOLATION
        return self.a+self.b

# Syntaxe correcte mais mauvaise qualité
obj = BadClass()
print(obj.m())''',
            "expected_issues": ["PEP8 violations", "no_docstring", "bad_formatting"],
            "difficulty": "easy"
        },
        
        # Fichier 3: Erreur de syntaxe
        f"{base_dir}/test_files/buggy_3.py": {
            "content": '''# Erreur de syntaxe
def broken_function(
    print("Hello"  # Parenthèse manquante - SYNTAX ERROR
    return 42

# Ce fichier ne peut même pas être exécuté''',
            "expected_issues": ["SyntaxError", "unclosed_parenthesis"],
            "difficulty": "medium"
        },
        
        # Fichier 4: Code propre (référence)
        f"{base_dir}/test_files/good_code.py": {
            "content": '''"""
Exemple de code propre - Data Officer
Fichier de référence pour tester que le système ne casse pas le code valide.
"""

def calculate_average(numbers):
    """
    Calcule la moyenne d'une liste de nombres.
    
    Args:
        numbers: Liste de nombres
        
    Returns:
        float: La moyenne
        
    Raises:
        ValueError: Si la liste est vide
    """
    if not numbers:
        raise ValueError("La liste ne peut pas être vide")
    
    return sum(numbers) / len(numbers)


def test_calculate_average():
    """Tests unitaires pour calculate_average."""
    # Test normal
    assert calculate_average([1, 2, 3, 4, 5]) == 3.0
    
    # Test avec nombres négatifs
    assert calculate_average([-1, 0, 1]) == 0.0
    
    # Test avec un seul élément
    assert calculate_average([42]) == 42.0
    
    print("✅ Tous les tests passent!")


if __name__ == "__main__":
    test_calculate_average()
    print("✨ Fichier de test exécuté avec succès")''',
            "expected_issues": [],
            "difficulty": "reference"
        }
    }
    
    # Créer les fichiers
    created_files = []
    for filepath, file_info in buggy_files.items():
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(file_info["content"])
        
        metadata["files"][os.path.basename(filepath)] = {
            "path": filepath,
            "issues": file_info["expected_issues"],
            "difficulty": file_info["difficulty"]
        }
        created_files.append(filepath)
        print(f"📄 Fichier créé: {filepath}")
    
    # 4. Créer un dataset de test simple (pour l'évaluation)
    dataset_files = {
        f"{base_dir}/test_dataset/simple_bug.py": '''def divide(a, b):
    return a / b  # Division par zéro possible

print(divide(10, 0))''',
        
        f"{base_dir}/test_dataset/style_issues.py": '''# Mauvais style - Data Officer
def f(x,y):
    z=x+y
    return z

class test:
    def m(self):
        pass''',
        
        f"{base_dir}/test_dataset/no_tests.py": '''def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Pas de tests unitaires - Data Officer''',
        
        f"{base_dir}/test_dataset/mixed_issues.py": '''# Fichier avec plusieurs problèmes
import sys,os  # Multiple imports

def bad(a,b):
    x=a+b
    if x>10:
        print("big")
    else:
        print("small")
    return x

# Code mort
unused_variable = 42'''
    }
    
    for filepath, content in dataset_files.items():
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        created_files.append(filepath)
        print(f"📄 Dataset créé: {filepath}")
    
    # 5. Créer des "hidden tests" (simuler l'évaluation)
    hidden_tests = {
        f"{base_dir}/hidden_tests/eval_1.py": '''# Test caché 1 - Boucle infinie potentielle
def problematic_loop(n):
    i = 0
    while i < n:  # Si n est négatif...
        i += 1
    return i

print(problematic_loop(-5))''',
        
        f"{base_dir}/hidden_tests/eval_2.py": '''# Test caché 2 - Problèmes de sécurité
import pickle

def unsafe_deserialize(data):
    return pickle.loads(data)  # DANGEREUX !

# Mauvaise pratique
user_input = input("Enter data: ")
unsafe_deserialize(user_input)'''
    }
    
    for filepath, content in hidden_tests.items():
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        created_files.append(filepath)
        print(f"🔒 Test caché créé: {filepath}")
    
    # 6. Sauvegarder les métadonnées
    metadata_file = f"{base_dir}/dataset_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Métadonnées sauvegardées: {metadata_file}")
    
    # 7. Afficher le rapport final
    print("\n" + "=" * 60)
    print("✅ SANDBOX CRÉÉ AVEC SUCCÈS!")
    print("=" * 60)
    
    print(f"\n📂 STRUCTURE CRÉÉE ({len(created_files)} fichiers):")
    print(f"{base_dir}/")
    print("├── test_files/")
    print("│   ├── buggy_1.py    # Division par zéro")
    print("│   ├── buggy_2.py    # Problèmes style PEP8")
    print("│   ├── buggy_3.py    # Erreur syntaxe")
    print("│   └── good_code.py  # Code propre (référence)")
    print("├── test_dataset/     # Pour tests système")
    print("├── hidden_tests/     # Simulation évaluation")
    print("└── dataset_metadata.json")
    
    print("\n🎯 UTILISATION:")
    print("Test basique: python main.py --target_dir sandbox/test_files")
    print("Test complet: python main.py --target_dir sandbox/test_dataset")
    print("Validation: python -m data_officer.log_validator")
    
    return {
        "success": True,
        "created_files": created_files,
        "metadata": metadata
    }


def create_minimal_dataset(output_dir: str = "sandbox/quick_test") -> list:
    """
    Crée un dataset minimal pour tests rapides.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    minimal_files = {
        f"{output_dir}/quick_bug.py": '''def buggy():
    x = 1 / 0  # Bug évident
    return x''',
        
        f"{output_dir}/quick_clean.py": '''def clean():
    """Fonction propre."""
    return 42'''
    }
    
    created = []
    for path, content in minimal_files.items():
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        created.append(path)
    
    print(f"✅ Dataset minimal créé: {output_dir}")
    return created


if __name__ == "__main__":
    create_sandbox_structure()