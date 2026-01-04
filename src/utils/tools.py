import os
import subprocess
import sys
from typing import List, Dict, Any
from pathlib import Path


def lire_fichier(chemin_fichier: str) -> str:
    """
    Lit le contenu d'un fichier (à partir de son chemin) et le retourne sous forme de chaîne 
    ou un message d'erreur.
    
    Args:
        chemin_fichier (str): Chemin vers le fichier à lire.
        
    Returns:
        str: Contenu du fichier ou message d'erreur.
    """
    try:
        chemin_fichier = os.path.normpath(chemin_fichier)

        if not os.path.isfile(chemin_fichier):
            return f"Erreur: Le chemin '{chemin_fichier}' ne correspond pas à un fichier."
        if not os.path.exists(chemin_fichier):
            return f"Erreur: Le chemin '{chemin_fichier}' n'existe pas."

        with open(chemin_fichier, 'r', encoding='utf-8') as fichier:
            return fichier.read()
    except PermissionError:
        return f"Erreur: Permission refusée lors de la lecture du fichier '{chemin_fichier}'."
    except UnicodeDecodeError:
        return f"Erreur: Impossible de décoder le fichier '{chemin_fichier}'. Ce n'est peut-être pas un fichier texte."
    except Exception as e:
        return f"Erreur: Une erreur inattendue s'est produite lors de la lecture du fichier '{chemin_fichier}': {str(e)}"


def ecrire_fichier(chemin_fichier: str, contenu: str) -> str:
    """
    Écrit un contenu dans un fichier.
    S'assure que l'écriture se fait uniquement dans le répertoire 'sandbox'.
    
    Args:
        chemin_fichier (str): Chemin vers le fichier où écrire le contenu.
        contenu (str): Contenu à écrire dans le fichier.
        
    Returns:
        str: Message de succès ou d'erreur.
    """
    try:
        chemin_fichier = os.path.normpath(chemin_fichier)

        # Vérifier si on écrit dans 'sandbox'
        sandbox_dir = os.path.normpath('sandbox')
        sandbox_absolu = os.path.abspath(sandbox_dir)
        cible_absolu = os.path.abspath(chemin_fichier)

        if not cible_absolu.startswith(sandbox_absolu):
            return f"Erreur: L'écriture n'est autorisée que dans le répertoire 'sandbox'."
        
        os.makedirs(os.path.dirname(chemin_fichier), exist_ok=True)
        
        # Si le fichier existe déjà, créer une sauvegarde
        chemin_sauvegarde = None
        if os.path.exists(chemin_fichier):
            chemin_sauvegarde = f"{chemin_fichier}.bak"
            with open(chemin_fichier, 'r', encoding='utf-8') as fichier_original:
                with open(chemin_sauvegarde, 'w', encoding='utf-8') as fichier_sauvegarde:
                    fichier_sauvegarde.write(fichier_original.read())

        with open(chemin_fichier, 'w', encoding='utf-8') as fichier:
            fichier.write(contenu)

        # Vérifier que l'écriture a réussi
        if os.path.exists(chemin_fichier):
            with open(chemin_fichier, 'r', encoding='utf-8') as fichier:
                contenu_ecrit = fichier.read()
                if contenu_ecrit == contenu:
                    return f"Succès: Contenu écrit dans '{chemin_fichier}'."
                else:
                    # Restaurer depuis la sauvegarde si l'écriture a échoué
                    if chemin_sauvegarde and os.path.exists(chemin_sauvegarde):
                        with open(chemin_sauvegarde, 'r', encoding='utf-8') as fichier_sauvegarde:
                            with open(chemin_fichier, 'w', encoding='utf-8') as fichier_original:
                                fichier_original.write(fichier_sauvegarde.read())
                    return f"Erreur: Échec de vérification. Le contenu dans '{chemin_fichier}' ne correspond pas au contenu attendu."
    except Exception as e:
        return f"Erreur: Une erreur inattendue s'est produite lors de l'écriture dans le fichier '{chemin_fichier}': {str(e)}"


def executer_pylint(chemin_fichier: str) -> str:
    """
    Exécute pylint sur un fichier Python donné et retourne les résultats.
    
    Args:
        chemin_fichier (str): Chemin vers le fichier Python à analyser.
        
    Returns:
        str: Sortie de pylint ou message d'erreur.
    """
    try:
        chemin_fichier = os.path.normpath(chemin_fichier)

        if not os.path.exists(chemin_fichier):
            return f"Erreur: Le fichier '{chemin_fichier}' n'existe pas."
        
        if not os.path.isfile(chemin_fichier):
            return f"Erreur: Le chemin '{chemin_fichier}' ne correspond pas à un fichier."
            
        if not chemin_fichier.endswith('.py'):
            return f"Erreur: Le fichier '{chemin_fichier}' n'est pas un fichier Python (.py requis)."

        print(f"[DEBUG] Exécution de pylint sur: {chemin_fichier}")
        
        # Exécuter pylint avec format texte
        resultat = subprocess.run(
            ['pylint', '--output-format=text', '--recursive=y', chemin_fichier],
            capture_output=True,
            text=True,
            timeout=30,  # Timeout de 30 secondes
            cwd=str(Path(chemin_fichier).parent) or '.',
            shell=False
        )
        
        # Construire la sortie complète
        parties_sortie = []
        
        # Ajouter la sortie de pylint
        if resultat.stdout:
            parties_sortie.append(f"RAPPORT D'ANALYSE PYLINT:\n{'='*50}")
            parties_sortie.append(resultat.stdout)
        
        # Ajouter les erreurs si présentes
        if resultat.stderr:
            parties_sortie.append(f"\nERREURS PYLINT:\n{'='*50}")
            parties_sortie.append(resultat.stderr)
        
        # Ajouter un résumé
        parties_sortie.append(f"\n{'='*50}")
        
        if resultat.returncode == 0:
            parties_sortie.append("RÉSUMÉ PYLINT: Aucun problème détecté !")
        else:
            # Analyser la sortie pour compter les problèmes
            lignes = resultat.stdout.split('\n') if resultat.stdout else []
            erreurs = sum(1 for ligne in lignes if ': E' in ligne)  # Erreurs
            avertissements = sum(1 for ligne in lignes if ': W' in ligne)  # Avertissements
            refactorisations = sum(1 for ligne in lignes if ': R' in ligne)  # Suggestions de refactorisation
            conventions = sum(1 for ligne in lignes if ': C' in ligne)  # Violations de conventions
            
            resume = f" RÉSUMÉ PYLINT: {erreurs} erreur(s), {avertissements} avertissement(s), "
            resume += f"{conventions} problème(s) de convention, {refactorisations} suggestion(s) de refactorisation."
            parties_sortie.append(resume)
        
        return "\n".join(parties_sortie)
        
    except subprocess.TimeoutExpired:
        return f"Erreur: Timeout de pylint après 30 secondes pour le fichier '{chemin_fichier}'. Le fichier pourrait être trop volumineux ou complexe."
    except FileNotFoundError:
        return "Erreur: Commande 'pylint' introuvable. Veuillez installer pylint: pip install pylint"
    except PermissionError:
        return f"Erreur: Permission refusée lors de l'exécution de pylint sur '{chemin_fichier}'."
    except Exception as e:
        return f"Erreur: Erreur inattendue lors de l'exécution de pylint sur '{chemin_fichier}': {str(e)}"



def executer_pytest(chemin_test: str) -> str:
    """
    Exécute pytest sur un fichier de test Python donné et retourne les résultats.
    
    Args:
        chemin_test (str): Chemin vers le fichier de test Python à exécuter.
        
    Returns:
        str: Sortie de pytest ou message d'erreur.
    """
    try:
        chemin_test = os.path.normpath(chemin_test)

        print(f"[DEBUG] Exécution de pytest sur : {chemin_test}")

        #Determiner les arguments pour pytest selon input
        if(os.path.isfile(chemin_test) and chemin_test.endswith('.py')):
            pytest_args = ['pytest', chemin_test,'-v', '--tb=short']
        elif(os.path.isdir(chemin_test)):
            pytest_args = ['pytest', chemin_test,'-v', '--tb=short']
        else:
            #si le chemin n'existe pas ou n'est pas un fichier/repertoire , executer dans le repertoire courant

            pytest_args = ['pytest', chemin_test,'-v', '--tb=short']
        # Exécuter pytest
        resultat = subprocess.run(
            pytest_args,
            capture_output=True,
            text=True,
            timeout=60,  # Timeout de 60 secondes
            shell=False
        )
        # Construire la sortie complète
        parties_sortie = []

        # Ajouter la sortie de pytest
        if resultat.stdout:
            parties_sortie.append(f"RAPPORT D'EXÉCUTION PYTEST:\n{'='*50}")
            #extraire uniquement la partie importante de la sortie
            lignes = resultat.stdout.split('\n')
            debut_idx = 0
            for i, ligne in enumerate(lignes):
                if ligne.startswith('============================= test session starts ============================='):
                    debut_idx = i
                    break

            if debut_idx < len(lignes):
                parties_sortie.append('\n'.join(lignes[debut_idx:]))    


        # Ajouter les erreurs si présentes
        if resultat.stderr:
            parties_sortie.append(f"\nERREURS PYTEST:\n{'='*50}")
            parties_sortie.append(resultat.stderr)

        # Ajouter un résumé
        parties_sortie.append(f"\n{'='*50}")   
        signification_code_sortie = {
            0: "Tous les tests ont réussi.",
            1: "Des tests ont échoué.",
            2: "Un problème est survenu lors de l'exécution des tests.",
            3: "Une erreur fatale est survenue lors de l'exécution de pytest .",
            4: "Pytest a été interrompu par l'utilisateur.",
            5: "Aucun test n'a été collecté."
        }
        resume = signification_code_sortie.get(resultat.returncode, "Code de sortie inconnu de pytest.")
        parties_sortie.append(f"RÉSUMÉ PYTEST: {resume}")

        #ajouter des stats si possible
        if resultat.stdout:
            for ligne in reversed(resultat.stdout.split('\n')):
                if "passed" in ligne.lower() and "failed" in ligne.lower():
                    parties_sortie.append(f"STATISTIQUES PYTEST: {ligne.strip()}")
                    break
        return "\n".join(parties_sortie)
    except subprocess.TimeoutExpired:
        return f"Erreur: Timeout de pytest après 60 secondes pour le chemin '{chemin_test}'. Le fichier pourrait être trop volumineux ou complexe."
    except FileNotFoundError:
        return "Erreur: Commande 'pytest' introuvable. Veuillez installer pytest: pip install pytest"
    except PermissionError:
        return f"Erreur: Permission refusée lors de l'exécution de pytest sur '{chemin_test}'."
    except Exception as e:
        return f"Erreur: Erreur inattendue lors de l'exécution de pytest sur '{chemin_test}': {str(e)}"


def lister_fichiers_python(repertoire: str) -> List[str]:
    """
    Liste tous les fichiers Python (.py) dans un répertoire donné.
    
    Args:
        repertoire (str): Chemin vers le répertoire à explorer.
        
    Returns:
        List[str]: Liste des chemins de fichiers Python.
    """
    try:
        repertoire = os.path.normpath(repertoire)

        if not os.path.exists(repertoire):
            return []
        fichiers_python = []
        for racine, repertoires, fichiers in os.walk(repertoire):
            #ignorer les repertoires indésirables
            repertoires[:] = [d for d in repertoires if d not in [
                '__pycache__', '.git', 'venv', '.venv',
                'node_modules', '.idea', '.vscode', 'logs'
            ]]
            for fichier in fichiers:
                if fichier.endswith('.py'):
                    chemin_complet = os.path.join(racine, fichier)
                    fichiers_python.append(chemin_complet)
        fichiers_python.sort()
        return fichiers_python
    except Exception as e:
        print(f"Erreur: Une erreur inattendue s'est produite lors de la liste des fichiers Python dans le répertoire '{repertoire}': {str(e)}", file=sys.stderr)
        return []


def obtenir_info_fichier(chemin_fichier: str) -> Dict[str, Any]:
    """
    Obtient des informations sur un fichier donné.
    
    Args:
        chemin_fichier (str): Chemin vers le fichier.
        
    Returns:
        Dict[str, Any]: Dictionnaire contenant les informations du fichier.
    """
    try:
        chemin_fichier = os.path.normpath(chemin_fichier)

        if not os.path.exists(chemin_fichier):
            return {"erreur": f"Le fichier '{chemin_fichier}' n'existe pas."}
        
        stats = os.stat(chemin_fichier)
        taille = stats.st_size
        if taille < 1024:
            taille_str = f"{taille} octets"
        elif taille < 1024 * 1024:
            taille_str = f"{taille / 1024:.2f} Ko"
        else:
            taille_str = f"{taille / (1024 * 1024):.2f} Mo"
        
        _, extension = os.path.splitext(chemin_fichier)
        return {
            "chemin": chemin_fichier,
            "chemins_absolu": os.path.abspath(chemin_fichier),
            "taille_octets": taille,
            "taille_humain": taille_str,
            "extension": extension,
            "est_fichier": os.path.isfile(chemin_fichier),
            "est_repertoire": os.path.isdir(chemin_fichier),
            "date_modification": stats.st_mtime,
            "nom": os.path.basename(chemin_fichier)
        }
    except Exception as e:
        return {"erreur": f"Une erreur inattendue s'est produite lors de l'obtention des informations du fichier '{chemin_fichier}': {str(e)}"}



def creer_fichier_test(nom_fichier: str, contenu: str = None) -> str:
    """
    Crée un fichier de test dans sandbox.
    
    Args:
        nom_fichier (str): Nom du fichier.
        contenu (str, optional): Contenu. Si None, crée un code d'exemple.
        
    Returns:
        str: Message de succès ou d'erreur.
    """
    try:
        if not nom_fichier.startswith("sandbox/"):
            nom_fichier = f"sandbox/{nom_fichier}"
        
        if contenu is None:
            contenu = '''"""
Fichier de test automatique.
"""

def exemple():
    """Fonction d'exemple."""
    return "test"

if __name__ == "__main__":
    print(exemple())'''
        
        return ecrire_fichier(nom_fichier, contenu)
        
    except Exception as e:
        return f"Erreur création fichier test: {str(e)}"
        