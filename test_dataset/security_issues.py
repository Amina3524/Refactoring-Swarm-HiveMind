import os
import subprocess

def execute_command(user_input):
    # Injection de commande possible
    os.system(f"echo {user_input}")
    
    # Plus dangereux encore
    subprocess.run(["rm", "-rf", user_input], shell=True)

def read_file(filename):
    # Path traversal possible
    with open(filename, 'r') as f:
        return f.read()

def eval_user_code(code):
    # DANGER: eval avec input utilisateur
    result = eval(code)
    return result

def sql_query(user_id):
    import sqlite3
    conn = sqlite3.connect('users.db')
    
    # Injection SQL
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor = conn.cursor()
    cursor.execute(query)
    
    return cursor.fetchall()

# Problèmes critiques de sécurité!