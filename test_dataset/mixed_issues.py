"""
Module de traitement de données
"""

import os, sys, json, math

data = []

def add_item(item):
    global data
    data.append(item)

def process_items():
    result = []
    for i in range(len(data)):
        for j in range(len(data)):
            if data[i] == data[j]:
                result.append(data[i])
    return result

class DataManager:
    def __init__(self, filename):
        self.filename = filename
        self.cache = {}
    
    def load(self):
        f = open(self.filename, 'r')
        content = f.read()
        f.close()
        
        try:
            return json.loads(content)
        except:
            return {}
    
    def save(self, data):
        with open(self.filename, 'w') as f:
            json.dump(data, f)
    
    def calculate_stats(self, numbers):
        total = 0
        for n in numbers:
            total += n
        
        avg = total / len(numbers)
        
        # Médiane mal calculée
        sorted_nums = sorted(numbers)
        mid = len(sorted_nums) // 2
        median = sorted_nums[mid]
        
        return {
            'total': total,
            'average': avg,
            'median': median
        }

# Test
if __name__ == "__main__":
    dm = DataManager("test.json")
    print(dm.calculate_stats([1, 2, 3, 4, 5]))
    
    # Problèmes:
    # - Variable globale
    # - Algorithme O(n²)
    # - Pas de gestion d'erreur pour fichier manquant
    # - Médiane mal calculée pour listes paires
    # - Fermeture de fichier manuelle au lieu de context manager