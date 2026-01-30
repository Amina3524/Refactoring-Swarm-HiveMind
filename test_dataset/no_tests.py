def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def is_prime(num):
    if num < 2:
        return False
    for i in range(2, int(num**0.5) + 1):
        if num % i == 0:
            return False
    return True

def validate_email(email):
    if "@" not in email:
        return False
    if "." not in email.split("@")[1]:
        return False
    return True

def format_phone(number):
    # Format: +33 X XX XX XX XX
    return f"+33 {number[:1]} {number[1:3]} {number[3:5]} {number[5:7]} {number[7:9]}"

# Problèmes:
# - Aucun test unitaire
# - Fonction fibonacci inefficace (récursivité naïve)
# - Validation email basique