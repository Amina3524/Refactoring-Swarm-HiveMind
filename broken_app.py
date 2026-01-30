def calculate_total(items):
    # Bug: missing input validation
    total=0
    for item in items:
        total=total+item["price"]*item["quantity"]
    return total

# No docstrings!
class OrderProcessor:
    def process(self, order):
        return calculate_total(order["items"])