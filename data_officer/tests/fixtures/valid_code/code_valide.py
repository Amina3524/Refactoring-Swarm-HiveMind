# valid_code/good_code.py
"""
Example of well-written Python code.
"""

def calculate_total(items):
    """Calculate total from list of items.
    
    Args:
        items: List of dicts with price and quantity
        
    Returns:
        Total sum
    """
    total = 0
    for item in items:
        total += item["price"] * item["quantity"]
    return total


class OrderProcessor:
    """Process orders and calculate totals."""
    
    def process(self, order):
        """Process an order.
        
        Args:
            order: Order dict with items
            
        Returns:
            Total amount
        """
        return calculate_total(order["items"])