"""
Test d'Exécution Pytest - Version COMPLÈTE
"""

import pytest
import os
import sys
import tempfile
import subprocess
import json

# === CONFIGURATION DES IMPORTS ===
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
src_path = os.path.join(project_root, "src")

# Vérifier si pytest est disponible
PYTEST_AVAILABLE = True

# Chercher le module pytest_runner
PYTEST_RUNNER_AVAILABLE = False
run_tests_func = None

if os.path.exists(src_path):
    sys.path.insert(0, src_path)
    print(f"✅ src/ trouvé: {src_path}")
    
    # Essayer d'importer
    try:
        from tools.pytest_runner import run_tests
        run_tests_func = run_tests
        PYTEST_RUNNER_AVAILABLE = True
        print("✅ run_tests importé")
    except ImportError as e:
        print(f"❌ Impossible d'importer pytest_runner: {e}")
else:
    print(f"❌ src/ non trouvé: {src_path}")

# Skip si non disponible
if not PYTEST_RUNNER_AVAILABLE or run_tests_func is None:
    pytestmark = pytest.mark.skip(reason="pytest_runner non disponible")


# ===== TESTS EXISTANTS (ne pas toucher) =====

class TestPytestExecution:
    """Tests de l'exécution de Pytest"""
    
    def test_pytest_execution_all_pass(self):
        """Tester l'exécution de tests qui passent tous"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 5
    assert add(0, 0) == 0
""")
            test_file = f.name
        
        try:
            result = run_tests_func(test_file)
            
            assert result.get("all_passed") == True
            assert result.get("failed", 1) == 0
            assert result.get("passed", 0) >= 1
        finally:
            os.unlink(test_file)
    
    def test_pytest_execution_with_failures(self):
        """Tester l'exécution de tests avec des échecs"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def multiply(a, b):
    return a + b  # Bug: should be *

def test_multiply():
    assert multiply(2, 3) == 6  # This will fail
""")
            test_file = f.name
        
        try:
            result = run_tests_func(test_file)
            
            assert result.get("all_passed") == False
            assert result.get("failed", 0) > 0
        finally:
            os.unlink(test_file)


# ===== NOUVEAUX TESTS (À AJOUTER) =====

def test_pytest_file_not_found():
    """Test pytest avec fichier inexistant"""
    result = run_tests_func("nonexistent_test_xyz_123.py")
    
    print(f"Résultat fichier inexistant: {result}")
    
    assert result.get("all_passed") == False
    assert result.get("failed") == 1
    assert result.get("passed") == 0

def test_pytest_exception_handling(monkeypatch):
    """Test gestion d'exception dans pytest"""
    # Mock qui simule une exception
    def mock_subprocess_run(*args, **kwargs):
        raise Exception("Mock exception: Cannot run pytest")
    
    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def test_example(): assert True")
        temp_file = f.name
    
    try:
        result = run_tests_func(temp_file)
        print(f"Résultat avec exception: {result}")
        
        assert result.get("all_passed") == False
        assert "error" in result
        assert "Mock exception" in result.get("error", "")
    finally:
        os.unlink(temp_file)

def test_pytest_timeout_handling(monkeypatch):
    """Test gestion de timeout"""
    def mock_subprocess_run(*args, **kwargs):
        import time
        time.sleep(35)  # Plus long que timeout de 30s
        raise subprocess.TimeoutExpired(cmd="pytest", timeout=30)
    
    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def test(): pass")
        temp_file = f.name
    
    try:
        result = run_tests_func(temp_file)
        print(f"Résultat timeout: {result}")
        
        assert result.get("all_passed") == False
        assert "error" in result
    finally:
        os.unlink(temp_file)

def test_pytest_empty_test_file():
    """Test avec fichier de test vide"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("")  # Fichier vide
        temp_file = f.name
    
    try:
        result = run_tests_func(temp_file)
        print(f"Résultat fichier vide: {result}")
        
        # Vérifier que ça ne crash pas
        assert isinstance(result, dict)
        assert "all_passed" in result
        # Peut retourner True ou False selon pytest
    finally:
        os.unlink(temp_file)

def test_pytest_invalid_python_file():
    """Test avec fichier Python invalide"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def test( : pass")  # Syntaxe invalide
        temp_file = f.name
    
    try:
        result = run_tests_func(temp_file)
        print(f"Résultat syntaxe invalide: {result}")
        
        # Vérifier que ça ne crash pas
        assert isinstance(result, dict)
    finally:
        os.unlink(temp_file)


# ===== TESTS BASIQUES (existants) =====

class TestPythonExecutionBasics:
    """Tests basiques d'exécution Python"""
    
    def test_python_script_runs(self):
        """Test qu'un script Python simple s'exécute"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import sys
print("Hello from test")
sys.exit(0)
""")
            script_file = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, script_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            assert result.returncode == 0
            assert "Hello from test" in result.stdout
        finally:
            os.unlink(script_file)
    
    def test_assertions_work(self):
        """Test que les assertions Python fonctionnent"""
        x = 5
        assert x == 5
        
        try:
            assert 2 + 2 == 5, "Math is broken"
            pytest.fail("Devrait lever AssertionError")
        except AssertionError as e:
            assert "Math is broken" in str(e)
    
    def test_import_data_officer_tools(self):
        """Test que les outils Data Officer peuvent être importés"""
        sys.path.append(os.path.join(project_root, "data_officer"))
        
        try:
            from validate_logs import validate_strict_format
            print("✅ validate_logs importé")
            
            # Test rapide
            test_logs = [{
                "timestamp": "2024-01-01T10:00:00",
                "agent": "Test",
                "model": "test",
                "action": "ANALYSIS",
                "details": {"input_prompt": "test", "output_response": "test"},
                "status": "SUCCESS"
            }]
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_logs, f)
                temp_file = f.name
            
            try:
                import validate_logs as vl
                original = vl.get_log_file_path
                vl.get_log_file_path = lambda: temp_file
                
                is_valid, errors, stats = validate_strict_format()
                print(f"Validation test: valid={is_valid}")
                
                vl.get_log_file_path = original
            finally:
                os.unlink(temp_file)
                
        except ImportError as e:
            pytest.fail(f"Impossible d'importer validate_logs: {e}")