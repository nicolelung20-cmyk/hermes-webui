"""Examples of efficient Fibonacci computation.

Run:
    python examples.py
"""

from __future__ import annotations


def fibonacci(n: int) -> int:
    """Return F(n) using fast doubling in O(log n) recursive steps."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an integer")
    if n < 0:
        raise ValueError("n must be nonnegative")

    def pair(k: int) -> tuple[int, int]:
        """Return (F(k), F(k + 1))."""
        if k == 0:
            return 0, 1

        a, b = pair(k // 2)
        c = a * (2 * b - a)
        d = a * a + b * b
        return (c, d) if k % 2 == 0 else (d, c + d)

    return pair(n)[0]


def fibonacci_iterative(n: int) -> int:
    """Return F(n) iteratively in O(n) steps and O(1) extra space."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an integer")
    if n < 0:
        raise ValueError("n must be nonnegative")

    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _self_test() -> None:
    expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
    assert [fibonacci(i) for i in range(len(expected))] == expected
    assert [fibonacci_iterative(i) for i in range(len(expected))] == expected
    assert fibonacci(100) == 354224848179261915075
    assert fibonacci(1000) > 0

    for fn in (fibonacci, fibonacci_iterative):
        try:
            fn(-1)
        except ValueError:
            pass
        else:
            raise AssertionError("negative input should raise ValueError")

        try:
            fn(2.5)  # type: ignore[arg-type]
        except TypeError:
            pass
        else:
            raise AssertionError("non-integer input should raise TypeError")


if __name__ == "__main__":
    _self_test()
    print("Fibonacci examples: all checks passed")
    print("First 10 values:", [fibonacci(i) for i in range(10)])
    print("F(1000) computed successfully using fast doubling.")
