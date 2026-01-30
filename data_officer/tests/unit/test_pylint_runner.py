"""
Test d'Exécution Pylint - Version COMPLÈTE
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

# Vérifier si pylint est disponible
try:
    import pylint
    PYLINT_AVAILABLE = True
    print("✅ Pylint installé")
except ImportError:
    PYLINT_AVAILABLE = False
    print("⚠️  Pylint non installé")

# Chercher le module pylint_runner
PYLINT_RUNNER_AVAILABLE = False
run_pylint_func = None
get_pylint_score_func = None

if os.path.exists(src_path):
    sys.path.insert(0, src_path)
    print(f"✅ src/ trouvé: {src_path}")
    
    # Essayer d'importer
    try:
        from tools.pylint_runner import run_pylint, get_pylint_score
        run_pylint_func = run_pylint
        get_pylint_score_func = get_pylint_score
        PYLINT_RUNNER_AVAILABLE = True
        print("✅ pylint_runner importé")
    except ImportError as e:
        print(f"❌ Impossible d'importer pylint_runner: {e}")
else:
    print(f"❌ src/ non trouvé: {src_path}")

# Skip si non disponible
if not PYLINT_AVAILABLE or not PYLINT_RUNNER_AVAILABLE:
    pytestmark = pytest.mark.skip(reason="Pylint ou pylint_runner non disponible")


# ===== TESTS EXISTANTS (ne pas toucher) =====

class TestPylintExecution:
    """Tests de l'exécution de Pylint"""
    
    @pytest.fixture
    def temp_python_file(self):
        """Créer un fichier Python temporaire"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            yield f.name
        
        # Nettoyage
        if os.path.exists(f.name):
            os.unlink(f.name)
    
    def test_pylint_execution_success(self, temp_python_file):
        """Tester que pylint s'exécute correctement"""
        with open(temp_python_file, 'w') as f:
            f.write("""
def add(a, b):
    '''Add two numbers'''
    return a + b
""")
        
        # Exécuter pylint
        result = run_pylint_func(temp_python_file)
        
        assert result.get("status") == "OK"
        assert result.get("score") is not None
        assert 0 <= result.get("score", -1) <= 10
    
    def test_pylint_score_calculation(self, temp_python_file):
        """Tester le calcul du score pylint"""
        with open(temp_python_file, 'w') as f:
            f.write("""
x=1  # Missing space around operator
def bad_function( ):  # Extra space
    pass
""")
        
        result = run_pylint_func(temp_python_file)
        
        # Le score doit être plus bas que le code propre
        assert result.get("score", 10) < 10
        assert result.get("issues", 0) > 0


# ===== NOUVEAUX TESTS (À AJOUTER) =====

def test_pylint_file_not_found():
    """Test pylint avec fichier inexistant"""
    result = run_pylint_func("nonexistent_file_xyz_123.py")
    
    print(f"Résultat fichier inexistant: {result}")
    
    assert result.get("status") == "FAILED"
    assert result.get("score") == 0
    assert result.get("issues") == 1

def test_pylint_exception_handling(monkeypatch):
    """Test gestion d'exception dans pylint"""
    # Mock qui simule une exception
    def mock_subprocess_run(*args, **kwargs):
        raise Exception("Mock exception: Cannot run pylint")
    
    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def test(): pass")
        temp_file = f.name
    
    try:
        result = run_pylint_func(temp_file)
        print(f"Résultat avec exception: {result}")
        
        assert result.get("status") == "FAILED"
        assert result.get("score") == 0
        assert "error" in result
        assert "Mock exception" in result.get("error", "")
    finally:
        os.unlink(temp_file)

def test_pylint_timeout_handling(monkeypatch):
    """Test gestion de timeout"""
    def mock_subprocess_run(*args, **kwargs):
        import time
        time.sleep(15)  # Plus long que timeout de 10s
        raise subprocess.TimeoutExpired(cmd="pylint", timeout=10)
    
    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def test(): pass")
        temp_file = f.name
    
    try:
        result = run_pylint_func(temp_file)
        print(f"Résultat timeout: {result}")
        
        assert result.get("status") == "FAILED"
        assert result.get("score") == 0
        assert "error" in result
    finally:
        os.unlink(temp_file)

def test_pylint_not_installed(monkeypatch):
    """Test quand pylint n'est pas installé"""
    def mock_subprocess_run(*args, **kwargs):
        raise FileNotFoundError("pylint command not found")
    
    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def test(): pass")
        temp_file = f.name
    
    try:
        result = run_pylint_func(temp_file)
        print(f"Résultat pylint non installé: {result}")
        
        assert result.get("status") == "FAILED"
        assert result.get("score") == 0
        assert "error" in result
    finally:
        os.unlink(temp_file)

def test_get_pylint_score_function():
    """Test de la fonction get_pylint_score"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def good_function(x):
    '''A good function'''
    return x * 2
""")
        temp_file = f.name
    
    try:
        score = get_pylint_score_func(temp_file)
        print(f"Score pylint: {score}")
        
        assert isinstance(score, float)
        assert 0 <= score <= 10
    finally:
        os.unlink(temp_file)

def test_pylint_empty_file():
    """Test avec fichier vide"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("")  # Fichier vide
        temp_file = f.name
    
    try:
        result = run_pylint_func(temp_file)
        print(f"Résultat fichier vide: {result}")
        
        # Vérifier que ça ne crash pas
        assert isinstance(result, dict)
        assert "status" in result
        assert "score" in result
    finally:
        os.unlink(temp_file)

def test_pylint_invalid_python_file():
    """Test avec fichier Python invalide"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def test( : pass")  # Syntaxe invalide
        temp_file = f.name
    
    try:
        result = run_pylint_func(temp_file)
        print(f"Résultat syntaxe invalide: {result}")
        
        # Vérifier que ça ne crash pas
        assert isinstance(result, dict)
        assert "status" in result
        # Peut être OK ou FAILED selon pylint
    finally:
        os.unlink(temp_file)

def test_pylint_score_improvement():
    """Test que le score s'améliore après correction"""
    # Créer un fichier avec mauvaise qualité
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
x=1
y=2
z=x+y
""")
        temp_file = f.name
    
    try:
        # Score avant
        score_before = get_pylint_score_func(temp_file)
        print(f"Score avant: {score_before}")
        
        # Corriger le fichier
        with open(temp_file, 'w') as f:
            f.write("""
x = 1
y = 2
z = x + y
""")
        
        # Score après
        score_after = get_pylint_score_func(temp_file)
        print(f"Score après: {score_after}")
        
        # Le score devrait être meilleur (ou égal)
        assert score_after >= score_before, f"Score n'a pas amélioré: {score_before} -> {score_after}"
        
    finally:
        os.unlink(temp_file)


# ===== TESTS DE QUALITÉ (existants) =====

class TestCodeQualityBasics:
    """Tests basiques de qualité de code"""
    
    def test_code_has_docstring(self):
        """Vérifier qu'une fonction a une docstring"""
        code_with_doc = '''
def my_function(x):
    """Cette fonction fait quelque chose"""
    return x * 2
'''
        
        code_without_doc = '''
def my_function(x):
    return x * 2
'''
        
        assert '"""' in code_with_doc or "'''" in code_with_doc
        assert not ('"""' in code_without_doc or "'''" in code_without_doc)
    
    def test_code_has_spaces_around_operators(self):
        """Vérifier les espaces autour des opérateurs"""
        good_code = "x = 1 + 2 * 3"
        bad_code = "x=1+2*3"
        
        assert " = " in good_code
        assert " + " in good_code
        assert " * " in good_code
        
        assert " = " not in bad_code
        assert " + " not in bad_code
        assert " * " not in bad_code
    
    def test_python_syntax(self):
        """Test basique de syntaxe Python"""
        valid_code = "def test():\n    pass"
        invalid_code = "def test(:\n    pass"  # Parenthèse manquante
        
        try:
            compile(valid_code, "<test>", "exec")
            print("✅ Code Python valide")
        except SyntaxError:
            pytest.fail("Code valide mais SyntaxError")
        
        try:
            compile(invalid_code, "<test>", "exec")
            pytest.fail("Devrait lever SyntaxError")
        except SyntaxError:
            print("✅ Code invalide détecté")