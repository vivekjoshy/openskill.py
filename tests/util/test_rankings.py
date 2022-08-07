from openskill import Rating
from openskill.util import rankings

a = "a"
b = "b"
c = "c"
d = "d"
e = "e"

r = Rating()


def test_rankings():
    assert rankings([], None) == []
    assert rankings([], []) == []
    assert rankings([a], [a]) == [0]
    assert rankings([a, b, c, d], None) == [0, 1, 2, 3]
    assert rankings([[a], [b]], [0, 0]) == [0, 0]
    assert rankings([a, b, c, d], [1, 2, 3, 4]) == [0, 1, 2, 3]
    assert rankings([a, b, c, d], [1, 1, 3, 4]) == [0, 0, 2, 3]
    assert rankings([a, b, c, d], [1, 2, 3, 3]) == [0, 1, 2, 2]
    assert rankings([a, b, c, d], [1, 2, 2, 4]) == [0, 1, 1, 3]
    assert rankings([a, b, c, d, e], [14, 32, 47, 47, 48]) == [0, 1, 2, 2, 4]
