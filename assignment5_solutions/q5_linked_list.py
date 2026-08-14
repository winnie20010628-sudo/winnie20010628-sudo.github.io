"""
Question 5 – Unordered singly-linked list

Numbers to add: 21, 35, 40, 50, 15, 8
Because add() inserts at the head, print order is: 8 15 50 40 35 21
"""


class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

    def get_data(self):
        return self.data

    def get_next(self):
        return self.next

    def set_data(self, data):
        self.data = data

    def set_next(self, next_node):
        self.next = next_node


class UnorderedList:
    def __init__(self):
        self.head = None

    def is_empty(self):
        return self.head is None

    def add(self, item):
        """Add a new node containing item at the head of the list."""
        temp = Node(item)
        temp.set_next(self.head)
        self.head = temp

    def size(self):
        current = self.head
        count = 0
        while current is not None:
            count += 1
            current = current.get_next()
        return count

    def print_list(self):
        current = self.head
        values = []
        while current is not None:
            values.append(str(current.get_data()))
            current = current.get_next()
        print(" ".join(values))

    def search(self, item):
        """Return True if item is in the list, otherwise False."""
        current = self.head
        while current is not None:
            if current.get_data() == item:
                return True
            current = current.get_next()
        return False


def demo_without_input():
    """Non-interactive demo matching the assignment sample output."""
    numbers = [21, 35, 40, 50, 15, 8]
    print(
        "Creating a linked list containing the following numbers: "
        + ", ".join(str(n) for n in numbers)
    )

    my_list = UnorderedList()
    for n in numbers:
        my_list.add(n)

    print("Displaying the contents of the list using the print_list() function")
    my_list.print_list()

    print("Testing the is_empty() function")
    print(my_list.is_empty())

    print("Testing the size() function")
    print(my_list.size())

    print()
    # Search demos from the assignment examples
    for target in [28, 50]:
        print(f"Please enter a number to search for in the list: {target}")
        print(my_list.search(target))


def interactive_search(my_list):
    """Allow the user to search for a number (for live screenshots)."""
    value = int(input("Please enter a number to search for in the list: "))
    print(my_list.search(value))


if __name__ == "__main__":
    demo_without_input()

    # Uncomment the lines below if you want live keyboard input for screenshots:
    # numbers = [21, 35, 40, 50, 15, 8]
    # my_list = UnorderedList()
    # for n in numbers:
    #     my_list.add(n)
    # interactive_search(my_list)
    # interactive_search(my_list)
