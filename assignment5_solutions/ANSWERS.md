# CS405 Assignment 5 — Complete Solutions

> **Important:** For Questions 4 and 6, replace `STUDENT_ID` in the Python files with your real 8-digit student ID before submitting screenshots.

---

## Section 1 – Algorithm Efficiency (Question 1)

### Algorithm 1: `calculate_iqr` — **O(n)**

```python
def calculate_iqr(sorted_data):
    def median(data):
        n = len(data)
        mid = n // 2
        if n % 2 == 0:
            return (data[mid - 1] + data[mid]) / 2
        else:
            return data[mid]

    n = len(sorted_data)
    mid = n // 2
    Q1 = median(sorted_data[:mid])
    Q3 = median(sorted_data[mid + (n % 2):])
    return Q3 - Q1
```

**Justification:** Let `n` be the length of `sorted_data`.

- `len()` and integer arithmetic are **O(1)**.
- The helper `median()` only indexes a few elements — **O(1)**.
- Slicing `sorted_data[:mid]` and `sorted_data[mid + (n % 2):]` each copies roughly half the list — **O(n)**.
- There are no nested loops over the data.

Overall time complexity is **O(n)**.

---

### Algorithm 2: `remove_duplicates` — **O(n²)**

```python
def remove_duplicates(arr):
    unique_list = []
    for num in arr:
        if num not in unique_list:
            unique_list.append(num)
    return unique_list
```

**Justification:** Let `n` be the length of `arr`.

- The outer loop runs once per element → **O(n)** iterations.
- Inside each iteration, `num not in unique_list` walks the growing list, which can contain up to `n` items → **O(n)** per check.
- Therefore total time is **O(n × n) = O(n²)**.

---

### Algorithm 3: `cal_ops` — **O(log N)**

```python
def cal_ops(N):
    i = N
    while i > 1:
        print(i, end=" ")
        number_of_operations += 1
        i = i // 2
    ...
```

**Justification:** The loop sets `i = i // 2` each time, so `i` halves every iteration.

- Starting from `N`, the sequence is roughly `N, N/2, N/4, …, 1`.
- The number of halvings needed to reach 1 is **⌊log₂ N⌋**.
- Each iteration does constant work (print + arithmetic).

Overall time complexity is **O(log N)**.

---

## Section 2 – Recursion (Question 2)

See `q2_sum_of_digits.py`.

```python
def sum_of_digits(n):
    if n < 10:
        return n
    return (n % 10) + sum_of_digits(n // 10)
```

- **Base case:** a single-digit number is already the sum.
- **Recursive case:** last digit (`n % 10`) + sum of the remaining digits (`n // 10`).
- Example: `12345` → `5 + 4 + 3 + 2 + 1` = **15**.

---

## Section 3 – Stacks (Question 3)

### Evaluate postfix

| | Expression | Working | Answer |
|---|---|---|---|
| **a)** | `3 7 - 9 *` | `(3 − 7) × 9 = (−4) × 9` | **−36** |
| **b)** | `7 3 8 * - 4 +` | `7 − (3 × 8) + 4 = 7 − 24 + 4` | **−13** |
| **c)** | `12 12 * 4 - 2 /` | `((12 × 12) − 4) / 2 = (144 − 4) / 2 = 140 / 2` | **70** |

### Convert infix → postfix

| | Infix | Postfix |
|---|---|---|
| **d)** | `5 + 2 * 7 – 2` | **`5 2 7 * + 2 -`** |
| **e)** | `7 + 2 * 9 / 5` | **`7 2 9 * 5 / +`** |
| **f)** | `(5 + 18) * (23 – 11) / (2 + 13)` | **`5 18 + 23 11 - * 2 13 + /`** |

*(Assumes standard precedence: `*` and `/` before `+` and `−`, left-to-right for equal precedence.)*

---

## Section 4 – Queues (Question 4)

See `q4_stack_queue.py`.

**Idea:** push each digit of your student ID onto a stack (LIFO), pop them into a queue (FIFO), then dequeue.

Because the stack reverses the digits and the queue keeps that reversed order, **emptying the queue prints the student ID digits in reverse**.

Example with ID `21405678`:

1. **Push onto stack (left → right):**  
   `2` → `2 1` → `2 1 4` → … → stack top is `8`
2. **Pop stack → enqueue:**  
   pop order: `8, 7, 6, 5, 0, 4, 1, 2`
3. **Empty queue:**  
   **`8 7 6 5 0 4 1 2`** (reversed student ID)

Replace `STUDENT_ID` in the script with yours, run it, and screenshot the step-by-step output for your logbook.

---

## Section 5 – Linked Lists (Question 5)

See `q5_linked_list.py`.

- Numbers to add (in this order): **21, 35, 40, 50, 15, 8**
- `add()` inserts at the **head**, so `print_list()` shows: **`8 15 50 40 35 21`**
- `is_empty()` → `False`
- `size()` → `6`
- `search(50)` → `True`; `search(28)` → `False`

---

## Section 6 – Sorting (Question 6)

See `q6_sorting.py`.

Use your 8-digit student ID as the list, e.g. ID `21405678` → `[2, 1, 4, 0, 5, 6, 7, 8]`.

- **Bubble sort:** print the list after each full pass.
- **Quick sort:** print the list after each partition pass (pivot placement).

Run the script and include the pass-by-pass output in your logbook.
