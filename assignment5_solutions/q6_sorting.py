"""
Question 6 – Bubble sort and Quick sort using student ID digits.

REPLACE the STUDENT_ID value below with your real 8-digit student ID
before taking screenshots for your logbook.
"""

# >>> CHANGE THIS TO YOUR STUDENT ID <<<
STUDENT_ID = "21405678"


def student_id_list(student_id):
    return [int(d) for d in student_id]


def bubble_sort(data):
    """Bubble sort that prints the list after each pass."""
    arr = data[:]
    n = len(arr)
    print("Bubble sort initial list:", arr)

    for pass_num in range(1, n):
        swapped = False
        for i in range(n - pass_num):
            if arr[i] > arr[i + 1]:
                arr[i], arr[i + 1] = arr[i + 1], arr[i]
                swapped = True
        print(f"After pass {pass_num}: {arr}")
        if not swapped:
            break

    print("Bubble sort final list:", arr)
    return arr


def quick_sort(data):
    """
    In-place quick sort that prints the whole list after each partition
    (i.e. after each pivot is placed in its final position).
    """
    arr = data[:]
    print("Quick sort initial list:", arr)
    pass_counter = {"count": 0}

    def partition(low, high):
        pivot = arr[high]
        i = low - 1
        for j in range(low, high):
            if arr[j] <= pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        return i + 1

    def _quick_sort(low, high):
        if low < high:
            pivot_index = partition(low, high)
            pass_counter["count"] += 1
            print(f"After pass {pass_counter['count']} (pivot={arr[pivot_index]}): {arr}")
            _quick_sort(low, pivot_index - 1)
            _quick_sort(pivot_index + 1, high)

    _quick_sort(0, len(arr) - 1)
    print("Quick sort final list:", arr)
    return arr


if __name__ == "__main__":
    numbers = student_id_list(STUDENT_ID)
    print(f"Student ID: {STUDENT_ID}")
    print(f"List of integers: {numbers}\n")

    print("=" * 50)
    print("BUBBLE SORT")
    print("=" * 50)
    bubble_sort(numbers)

    print()
    print("=" * 50)
    print("QUICK SORT")
    print("=" * 50)
    quick_sort(numbers)
