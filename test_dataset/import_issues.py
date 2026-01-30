import os
import sys

# Import circulaire potentiel
from utils.helpers import process_data

# Import inutilisé
import datetime
import random

def read_json_file(filepath):
    # json n'est pas importé !
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data

def calculate_statistics():
    # pandas n'est pas importé
    import pandas as pd  # Import dans la fonction
    
    df = pd.DataFrame({'values': [1, 2, 3]})
    return df.mean()

def plot_data():
    # matplotlib n'est pas importé
    import matplotlib.pyplot as plt
    
    x = [1, 2, 3]
    y = [4, 5, 6]
    plt.plot(x, y)
    plt.show()

# Problèmes:
# - Import manquant (json)
# - Import inutilisé (datetime, random)
# - Import dans le corps des fonctions