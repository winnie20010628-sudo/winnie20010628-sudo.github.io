"""
Question 2 – Recursive sum of digits
Example: sum_of_digits(12345) -> 15
"""


def sum_of_digits(n):
    """Return the sum of digits of a positive natural number using recursion."""
    if n < 10:
        return n  # base case: single digit
    return (n % 10) + sum_of_digits(n // 10)


if __name__ == "__main__":
    number = 12345
    print(f"Input: {number}")
    print(f"Output: {sum_of_digits(number)}")

    # Extra checks
    for test in [7, 99, 100, 98765]:
        print(f"sum_of_digits({test}) = {sum_of_digits(test)}")
