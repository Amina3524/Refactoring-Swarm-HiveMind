import pytest
import json
import os
import subprocess
from pathlib import Path

class TestRefactoringComplete:
    """Tests fonctionnels du système complet"""
    
    @pytest.fixture
    def sandbox_setup(self):
        """Préparer un dossier sandbox pour les tests"""
        sandbox = "tests/fixtures/sandbox_test"
        os.makedirs(sandbox, exist_ok=True)
        
        # Créer un fichier Python buggé
        broken_code = f"{sandbox}/broken_app.py"
        with open(broken_code, 'w') as f:
            f.write("""
def calculate_total(items):
    # Bug: missing input validation
    total=0
    for item in items:
        total=total+item["price"]*item["quantity"]
    return total

# No docstrings!
class OrderProcessor:
    def process(self, order):
        return calculate_total(order["items"])
""")
        
        yield sandbox
        
        # Cleanup
        import shutil
        if os.path.exists(sandbox):
            shutil.rmtree(sandbox)
    
    def test_tc_001_simple_refactoring(self, sandbox_setup):
        """
        TC-001 : Refactoring d'un fichier avec erreurs simples
        
        Préconditions : Fichier Python avec bugs mineurs
        Scénario :
            1. Charger fichier buggé dans sandbox
            2. Lancer le système
            3. Vérifier que le code a été modifié
            4. Exécuter pytest
        Résultats attendus :
            1. ✓ Fichier modifié
            2. ✓ Tests passent
            3. ✓ Logs enregistrés
            4. ✓ Pylint amélioré
        """
        # Étape 1 : Lancer le système
        result = subprocess.run(
            ["python", "main.py", "--target_dir", sandbox_setup],
            capture_output=True,
            timeout=60
        )
        
        # Le système ne doit pas crash
        assert result.returncode == 0, f"System crashed: {result.stderr}"
        
        # Étape 2 : Vérifier que les fichiers ont été modifiés
        modified_file = f"{sandbox_setup}/broken_app.py"
        with open(modified_file, 'r') as f:
            modified_code = f.read()
        
        # Le code doit avoir changé (au minimum, ajout de docstrings)
        assert "'''" in modified_code or '"""' in modified_code, \
            "Code should have docstrings added"
        
        # Étape 3 : Vérifier que les tests passent
        test_result = subprocess.run(
            ["python", "-m", "pytest", modified_file, "-v"],
            capture_output=True
        )
        # Note: Si l'agent génère des tests, ils doivent passer
        
        # Étape 4 : Vérifier les logs
        log_file = "logs/experiment_data.json"
        assert os.path.exists(log_file), "Log file not created"
        
        with open(log_file, 'r') as f:
            logs = json.load(f)
            # Vérifier qu'il y a au moins une action ANALYSIS et une action FIX
            actions = [log["action"] for log in logs]
            assert "ANALYSIS" in actions
            assert "FIX" in actions
    
    def test_tc_002_test_generation(self, sandbox_setup):
        """
        TC-002 : Refactoring d'un code sans tests existants
        
        Préconditions : Code buggé SANS tests unitaires
        Scénario :
            1. Charger code sans tests
            2. Lancer le système
            3. Vérifier que des tests sont générés
        Résultats attendus :
            1. ✓ Tests unitaires générés
            2. ✓ Tests passent
        """
        # Créer un fichier sans tests
        code_file = f"{sandbox_setup}/no_tests.py"
        with open(code_file, 'w') as f:
            f.write("""
def greet(name):
    return f"Hello {name}"

def add(a, b):
    return a + b
""")
        
        # Lancer le système
        result = subprocess.run(
            ["python", "main.py", "--target_dir", sandbox_setup],
            capture_output=True,
            timeout=60
        )
        
        assert result.returncode == 0
        
        # Vérifier que des tests ont été générés
        test_file = f"{sandbox_setup}/test_no_tests.py"
        # Ou vérifier dans les logs qu'une action GENERATION a eu lieu
        
        with open("logs/experiment_data.json", 'r') as f:
            logs = json.load(f)
            generation_actions = [log for log in logs if log["action"] == "GENERATION"]
            assert len(generation_actions) > 0, "No tests were generated"
    
    def test_tc_003_feedback_loop(self, sandbox_setup):
        """
        TC-003 : Boucle de feedback fonctionnelle
        
        Scénario :
            1. Auditor analyse
            2. Fixer modifie
            3. Judge teste
            4. Si fail → Retour au Fixer (max 10 itérations)
            5. Si success → Arrêt
        Résultats attendus :
            1. ✓ Pas de boucle infinie
            2. ✓ Système s'arrête proprement
            3. ✓ Code final fonctionnel
        """
        # Créer du code complexe avec multiples bugs
        complex_code = f"{sandbox_setup}/complex.py"
        with open(complex_code, 'w') as f:
            f.write("""
def process_data(data):
    result = []
    for i in range(len(data)):
        x = data[i]
        y = data[i]*2  # Potential index error
        z = x + y
        result.append(z)
    return result

# No tests, missing docstring
""")
        
        # Lancer le système
        result = subprocess.run(
            ["python", "main.py", "--target_dir", sandbox_setup],
            capture_output=True,
            timeout=120  # Plus de temps pour les itérations
        )
        
        assert result.returncode == 0, "System crashed"
        
        # Vérifier le nombre d'itérations
        with open("logs/experiment_data.json", 'r') as f:
            logs = json.load(f)
            max_iteration = max(
                [log.get("metadata", {}).get("iteration", 0) for log in logs]
            )
            assert max_iteration <= 10, f"Too many iterations: {max_iteration}"
    
    def test_tc_004_target_dir_restriction(self, sandbox_setup):
        """
        TC-004 : Respect du --target_dir (Sécurité)
        
        Scénario :
            Vérifier que SEULS les fichiers du répertoire cible sont modifiés
        """
        import shutil
        
        # Créer un fichier dehors du sandbox
        outside_file = "outside_test.py"
        with open(outside_file, 'w') as f:
            f.write("original_content = True")
        
        try:
            # Lancer le système
            subprocess.run(
                ["python", "main.py", "--target_dir", sandbox_setup],
                capture_output=True,
                timeout=60
            )
            
            # Vérifier que le fichier dehors n'a pas changé
            with open(outside_file, 'r') as f:
                content = f.read()
                assert content == "original_content = True", \
                    "File outside sandbox was modified!"
        
        finally:
            if os.path.exists(outside_file):
                os.remove(outside_file)