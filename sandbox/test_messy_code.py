def is_value_in_range(value):
    """
    Checks if a given value is strictly between 0 and 100 (exclusive).

    Args:
        value (int | float): The number to check.

    Returns:
        bool: True if the value is greater than 0 and less than 100, False otherwise.
    """
    return 0 < value < 100