def find_duplicates(items):
    # O(n²) inefficace
    duplicates = []
    for i in range(len(items)):
        for j in range(len(items)):
            if i != j and items[i] == items[j]:
                if items[i] not in duplicates:
                    duplicates.append(items[i])
    return duplicates

def process_large_list(data):
    # Copie inutile de liste
    result = []
    temp = data[:]  # Copie
    
    for item in temp:
        processed = expensive_operation(item)
        result.append(processed)
    
    # Tri à chaque itération
    result.sort()
    
    return result

def expensive_operation(n):
    # Calcul coûteux
    total = 0
    for i in range(1000000):
        total += i * n
    return total

def get_user_data(user_ids):
    # N+1 query problem
    import sqlite3
    conn = sqlite3.connect('database.db')
    
    results = []
    for user_id in user_ids:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
        results.append(cursor.fetchone())
    
    return results