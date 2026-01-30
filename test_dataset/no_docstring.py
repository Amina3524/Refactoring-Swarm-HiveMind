def process_data(data):
    result = []
    for item in data:
        if item % 2 == 0:
            result.append(item * 2)
        else:
            result.append(item + 1)
    return result

def validate_user(username, password):
    if len(username) < 3:
        return False
    if len(password) < 6:
        return False
    return True

def calculate_stats(numbers):
    total = sum(numbers)
    average = total / len(numbers)
    max_val = max(numbers)
    min_val = min(numbers)
    return total, average, max_val, min_val

# Problèmes:
# - Aucune docstring
# - Pas de type hints
# - Code non commenté