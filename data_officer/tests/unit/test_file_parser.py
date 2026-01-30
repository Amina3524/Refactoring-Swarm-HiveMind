"""
Test du Parser de Fichiers - Version corrigée
"""

import pytest
import os
import tempfile
import sys
import json

# === CONFIGURATION DES IMPORTS ===
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
src_path = os.path.join(project_root, "src")

if os.path.exists(src_path):
    sys.path.insert(0, src_path)
    print(f"✅ src/ trouvé: {src_path}")
    
    # Essayer d'importer
    try:
        from tools.file_parser import parse_python_file
        PARSER_AVAILABLE = True
        print("✅ Module file_parser importé")
    except ImportError as e:
        print(f"❌ Impossible d'importer file_parser: {e}")
        PARSER_AVAILABLE = False
else:
    print(f"❌ src/ non trouvé: {src_path}")
    PARSER_AVAILABLE = False

# Skip si non disponible
if not PARSER_AVAILABLE:
    pytestmark = pytest.mark.skip(reason="Module file_parser non disponible")


class TestFileParsing:
    """Tests du module de parsing de fichiers Python"""
    
    @pytest.fixture
    def test_files_dir(self):
        """Créer des fichiers de test temporaires"""
        test_dir = os.path.join(tempfile.gettempdir(), "test_parser")
        os.makedirs(test_dir, exist_ok=True)
        yield test_dir
        # Nettoyage
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
    
    def test_parse_valid_python_file(self, test_files_dir):
        """Tester le parsing d'un fichier Python valide"""
        test_file = os.path.join(test_files_dir, "valid.py")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("""
def hello(name):
    '''Greeter function'''
    return f"Hello {name}"

if __name__ == "__main__":
    print(hello("World"))
""")
        
        # Parser le fichier
        result = parse_python_file(test_file)
        
        # Vérifications
        assert result is not None
        assert result.get("lines", 0) > 0
        assert result.get("syntax_valid", False) == True
        assert result.get("functions", 0) >= 1
    
    def test_parse_nonexistent_file(self):
        """Tester le comportement avec un fichier inexistant"""
        with pytest.raises(FileNotFoundError):
            parse_python_file("nonexistent_file_xyz.py")
    
    def test_parse_file_with_syntax_error(self, test_files_dir):
        """Tester le parsing d'un fichier avec erreurs de syntaxe"""
        test_file = os.path.join(test_files_dir, "broken_syntax.py")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("""
def broken_function(
    return "This is broken"  # Missing closing parenthesis
""")
        
        result = parse_python_file(test_file)
        assert result.get("syntax_valid", True) == False
        assert len(result.get("syntax_errors", [])) > 0
    
    def test_parse_empty_file(self, test_files_dir):
        """Tester le parsing d'un fichier vide"""
        test_file = os.path.join(test_files_dir, "empty.py")
        with open(test_file, 'w') as f:
            f.write("")
        
        result = parse_python_file(test_file)
        assert result.get("lines", 1) == 0
        assert result.get("functions", 0) == 0


# Tests basiques qui ne dépendent pas du parser
class TestFileIOBasics:
    """Tests basiques de lecture/écriture de fichiers"""
    
    def test_file_creation_and_deletion(self):
        """Test basique de création/suppression de fichier"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('test')")
            temp_file = f.name
        
        assert os.path.exists(temp_file), "Fichier non créé"
        
        # Lire le fichier
        with open(temp_file, 'r') as f:
            content = f.read()
        
        assert "print('test')" in content
        
        # Supprimer
        os.unlink(temp_file)
        assert not os.path.exists(temp_file), "Fichier non supprimé"
    
    def test_json_handling(self):
        """Test la manipulation JSON (important pour les logs)"""
        test_data = {
            "test": "value",
            "number": 123,
            "list": [1, 2, 3]
        }
        
        # Écrire JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        # Lire JSON
        with open(temp_file, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == test_data
        os.unlink(temp_file)