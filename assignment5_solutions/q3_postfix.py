"""
Question 3 – Postfix evaluation helpers (optional verification).
Written answers are in ANSWERS.md.
"""


def evaluate_postfix(expression):
    """Evaluate a space-separated postfix expression."""
    stack = []
    for token in expression.split():
        if token in {"+", "-", "*", "/"}:
            b = stack.pop()
            a = stack.pop()
            if token == "+":
                stack.append(a + b)
            elif token == "-":
                stack.append(a - b)
            elif token == "*":
                stack.append(a * b)
            else:
                stack.append(a / b)
        else:
            stack.append(float(token) if "." in token else int(token))
    return stack[0]


def infix_to_postfix(expression):
    """Convert an infix expression (tokens space-separated) to postfix."""
    precedence = {"+": 1, "-": 1, "*": 2, "/": 2}
    output = []
    ops = []

    for token in expression.replace("–", "-").split():
        if token.isdigit() or (token[0] == "-" and token[1:].isdigit()):
            output.append(token)
        elif token == "(":
            ops.append(token)
        elif token == ")":
            while ops and ops[-1] != "(":
                output.append(ops.pop())
            ops.pop()
        else:
            while (
                ops
                and ops[-1] != "("
                and precedence.get(ops[-1], 0) >= precedence.get(token, 0)
            ):
                output.append(ops.pop())
            ops.append(token)

    while ops:
        output.append(ops.pop())
    return " ".join(output)


if __name__ == "__main__":
    print("=== Postfix evaluation ===")
    cases = [
        ("a", "3 7 - 9 *"),
        ("b", "7 3 8 * - 4 +"),
        ("c", "12 12 * 4 - 2 /"),
    ]
    for label, expr in cases:
        print(f"{label}) {expr}  =>  {evaluate_postfix(expr)}")

    print("\n=== Infix to postfix ===")
    infix_cases = [
        ("d", "5 + 2 * 7 - 2"),
        ("e", "7 + 2 * 9 / 5"),
        ("f", "( 5 + 18 ) * ( 23 - 11 ) / ( 2 + 13 )"),
    ]
    for label, expr in infix_cases:
        print(f"{label}) {expr}  =>  {infix_to_postfix(expr)}")
