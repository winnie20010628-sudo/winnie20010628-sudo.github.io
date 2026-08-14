"""
Question 4 – Stack then Queue using student ID digits.

REPLACE the STUDENT_ID value below with your real 8-digit student ID
before taking screenshots for your logbook.
"""

# >>> CHANGE THIS TO YOUR STUDENT ID <<<
STUDENT_ID = "21405678"


class Stack:
    def __init__(self):
        self.items = []

    def is_empty(self):
        return len(self.items) == 0

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self.items.pop()

    def peek(self):
        return self.items[-1]

    def __str__(self):
        # show bottom -> top
        return "Stack (bottom -> top): " + str(self.items)


class Queue:
    def __init__(self):
        self.items = []

    def is_empty(self):
        return len(self.items) == 0

    def enqueue(self, item):
        self.items.append(item)

    def dequeue(self):
        if self.is_empty():
            raise IndexError("dequeue from empty queue")
        return self.items.pop(0)

    def __str__(self):
        # show front -> rear
        return "Queue (front -> rear): " + str(self.items)


def main():
    stack = Stack()
    queue = Queue()

    print(f"Student ID: {STUDENT_ID}")
    print("Both stack and queue start empty.\n")

    # Step 1: push each digit onto the stack
    print("=== STEP 1: Push student ID digits onto the Stack ===")
    for digit in STUDENT_ID:
        stack.push(int(digit))
        print(f"  push {digit}  ->  {stack}")

    # Step 2: empty the stack into the queue
    print("\n=== STEP 2: Empty Stack and enqueue each value into the Queue ===")
    while not stack.is_empty():
        value = stack.pop()
        queue.enqueue(value)
        print(f"  pop {value} from stack, enqueue into queue")
        print(f"       {stack}")
        print(f"       {queue}")

    # Step 3: empty the queue
    print("\n=== STEP 3: Empty the Queue ===")
    output = []
    while not queue.is_empty():
        value = queue.dequeue()
        output.append(value)
        print(f"  dequeue {value}  ->  remaining {queue}")

    print("\n=== FINAL OUTPUT (emptied Queue) ===")
    print(" ".join(str(d) for d in output))
    print(f"(This is the student ID digits in reverse order)")


if __name__ == "__main__":
    main()
