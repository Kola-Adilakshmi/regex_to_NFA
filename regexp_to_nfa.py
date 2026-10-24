
class State:
    def __init__(self, name):
        self.name = name
        self.transitions = {}


class NFA:
    def __init__(self, start, accept):
        self.start = start
        self.accept = accept


state_count = 0


def new_state():
    global state_count
    state_count += 1
    return State(f"q{state_count}")


def add_transition(source, symbol, destination):
    source.transitions.setdefault(symbol, set()).add(destination)


def tokenize_regex(regex):
    tokens = []

    for char in regex:
        if char.isspace():
            continue

        if char.isalnum() or char in "_":
            tokens.append(char)
        elif char in "()|*":
            tokens.append(char)
        else:
            raise ValueError(f"Unsupported character: {char}")

    # Insert explicit concatenation operator '.'
    result = []

    for i, token in enumerate(tokens):
        if i > 0:
            previous = tokens[i - 1]

            if (
                previous not in ("(", "|")
                and token not in (")", "|", "*")
            ):
                result.append(".")

        result.append(token)

    return result


def to_postfix(tokens):
    precedence = {"|": 1, ".": 2}
    output = []
    operators = []

    for token in tokens:
        if token not in ("|", ".", "*", "(", ")"):
            output.append(token)

        elif token == "(":
            operators.append(token)

        elif token == ")":
            while operators and operators[-1] != "(":
                output.append(operators.pop())

            if not operators:
                raise ValueError("Mismatched parentheses.")

            operators.pop()

        elif token == "*":
            output.append(token)

        else:
            while (
                operators
                and operators[-1] != "("
                and precedence[operators[-1]] >= precedence[token]
            ):
                output.append(operators.pop())

            operators.append(token)

    if "(" in operators:
        raise ValueError("Mismatched parentheses.")

    while operators:
        output.append(operators.pop())

    return output


def build_nfa(postfix):
    stack = []

    for token in postfix:
        if token not in ("|", ".", "*"):
            start = new_state()
            accept = new_state()
            add_transition(start, token, accept)
            stack.append(NFA(start, accept))

        elif token == ".":
            if len(stack) < 2:
                raise ValueError("Invalid concatenation.")

            second = stack.pop()
            first = stack.pop()

            add_transition(first.accept, "ε", second.start)
            stack.append(NFA(first.start, second.accept))

        elif token == "|":
            if len(stack) < 2:
                raise ValueError("Invalid union operator.")

            second = stack.pop()
            first = stack.pop()

            start = new_state()
            accept = new_state()

            add_transition(start, "ε", first.start)
            add_transition(start, "ε", second.start)
            add_transition(first.accept, "ε", accept)
            add_transition(second.accept, "ε", accept)

            stack.append(NFA(start, accept))

        elif token == "*":
            if not stack:
                raise ValueError("Invalid repetition operator.")

            inner = stack.pop()
            start = new_state()
            accept = new_state()

            add_transition(start, "ε", inner.start)
            add_transition(start, "ε", accept)
            add_transition(inner.accept, "ε", inner.start)
            add_transition(inner.accept, "ε", accept)

            stack.append(NFA(start, accept))

    if len(stack) != 1:
        raise ValueError("Invalid regular expression.")

    return stack[0]


def epsilon_closure(states):
    closure = set(states)
    pending = list(states)

    while pending:
        state = pending.pop()

        for destination in state.transitions.get("ε", set()):
            if destination not in closure:
                closure.add(destination)
                pending.append(destination)

    return closure


def move(states, symbol):
    result = set()

    for state in states:
        result.update(state.transitions.get(symbol, set()))

    return result


def simulate(nfa, string):
    current = epsilon_closure({nfa.start})

    for char in string:
        current = epsilon_closure(move(current, char))

    return nfa.accept in current


def print_nfa(start):
    print("\nNFA TRANSITIONS")
    print("-" * 45)

    visited = set()
    pending = [start]

    while pending:
        state = pending.pop()

        if state in visited:
            continue

        visited.add(state)

        for symbol, destinations in state.transitions.items():
            for destination in destinations:
                print(
                    f"{state.name} --{symbol}--> "
                    f"{destination.name}"
                )
                pending.append(destination)


print("REGULAR EXPRESSION TO NFA SIMULATOR")
print("=" * 45)

try:
    regex = input("Enter a regular expression: ").strip()

    if not regex:
        raise ValueError("Regular expression cannot be empty.")

    state_count = 0
    postfix = to_postfix(tokenize_regex(regex))
    nfa = build_nfa(postfix)

    print("Start state:", nfa.start.name)
    print("Accept state:", nfa.accept.name)
    print("Postfix expression:", " ".join(postfix))

    print_nfa(nfa.start)

    while True:
        string = input(
            "\nEnter a string to test (or type EXIT): "
        )

        if string.upper() == "EXIT":
            break

        if simulate(nfa, string):
            print("ACCEPTED: String belongs to the language.")
        else:
            print("REJECTED: String does not belong to the language.")

except ValueError as error:
    print("Error:", error)
