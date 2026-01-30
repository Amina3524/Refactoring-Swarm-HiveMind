def find_max(numbers):
    # Bug: Ne fonctionne pas si la liste est vide
    max_num = numbers[0]
    for num in numbers:
        if num > max_num:
            max_num = num
    return max_num

def divide_numbers(a, b):
    # Bug: Pas de vérification division par zéro
    return a / b

def count_vowels(text):
    # Bug: Compter incorrectement
    vowels = "aeiou"
    count = 0
    for char in text:
        if char in vowels:
            count += 1
        else:
            count = count  # Ligne inutile
    return count

def process_list(items):
    # Bug: Modifie la liste originale
    for i in range(len(items)):
        items[i] = items[i] * 2
    return items

# Tests qui échoueront:
print(find_max([]))  # IndexError
print(divide_numbers(10, 0))  # ZeroDivisionError