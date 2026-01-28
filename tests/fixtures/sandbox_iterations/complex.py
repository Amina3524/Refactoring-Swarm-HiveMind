
def algorithm(n):
    if n <= 1:
        return n
    return algorithm(n-1) + algorithm(n-2)
