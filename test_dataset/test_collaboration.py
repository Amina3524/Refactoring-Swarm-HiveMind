"""
test_collaboration.py

Fichier spécialement conçu pour tester la collaboration entre agents.
Il contient des problèmes qui nécessitent l'intervention des 3 agents.
"""

# 1. Problème détecté par l'Auditor
def calculate_average(numbers):
    # Pas de vérification de liste vide
    total = sum(numbers)
    return total / len(numbers)  # Division par zero possible

# 2. Problème de style que le Fixer doit corriger
def process_data ( data_list ) :
    result=[]
    for item in data_list :
        if item %2==0:
            result.append(item*2)
        else:
            result.append(item+1)
    return result

# 3. Code qui nécessite des tests (Judge)
def validate_email(email):
    # Validation basique
    if "@" in email:
        return True
    return False

# 4. Problème complexe nécessitant plusieurs passes
class UserManager:
    def __init__(self):
        self.users = []
    
    def add_user(self, name, email):
        # Problèmes multiples:
        # - Pas de validation d'email
        # - Pas de vérification de doublon
        # - Pas de docstring
        user = {"name": name, "email": email}
        self.users.append(user)
    
    def find_user(self, name):
        # Algorithme inefficace O(n)
        for user in self.users:
            if user["name"] == name:
                return user
        return None

# 5. Test qui échouera initialement
def test_calculate_average():
    # Ce test va échouer, déclenchant le feedback loop
    assert calculate_average([1, 2, 3]) == 2
    assert calculate_average([]) == 0  # Va causer ZeroDivisionError

# Points à observer:
# 1. Auditor doit détecter: 
#    - Pas de docstrings
#    - Pas de type hints  
#    - Division par zero possible
#    - Algorithme inefficace
# 2. Fixer doit:
#    - Ajouter docstrings
#    - Ajouter type hints
#    - Corriger division par zero
#    - Optimiser find_user
# 3. Judge doit:
#    - Exécuter les tests
#    - Si échec: renvoyer au Fixer
#    - Si succès: valider

if __name__ == "__main__":
    # Exécuter les tests (va échouer)
    test_calculate_average()
    print("All tests passed!")