import random

from openskill.util import unwind


def test_unwind():
    # Zero Items
    src = []
    rank = []
    dst, de_rank = unwind(rank, src)
    assert dst is None
    assert de_rank is None

    # Accepts 1 Item
    src = ["a"]
    rank = [0]
    dst, de_rank = unwind(rank, src)
    assert dst == ["a"]
    assert de_rank == [0]

    # Accepts 2 Items
    src = ["b", "a"]
    rank = [1, 0]
    dst, de_rank = unwind(rank, src)
    assert dst == ["a", "b"]
    assert de_rank == [1, 0]

    # Accepts 3 Items
    src = ["b", "c", "a"]
    rank = [1, 2, 0]
    dst, de_rank = unwind(rank, src)
    assert dst == ["a", "b", "c"]
    assert de_rank == [2, 0, 1]

    # Accepts 4 Items
    src = ["b", "d", "c", "a"]
    rank = [1, 3, 2, 0]
    dst, de_rank = unwind(rank, src)
    assert dst == ["a", "b", "c", "d"]
    assert de_rank == [3, 0, 2, 1]

    # Can undo the ranking
    src = [random.random() for i in range(100)]
    random.shuffle(src)
    rank = [i for i in range(100)]
    trans, de_rank = unwind(rank, src)
    dst, de_de_rank = unwind(de_rank, trans)
    assert src == dst
    assert de_de_rank == rank

    # Allows ranks that are not zero-indexed integers
    src = ["a", "b", "c", "d", "e", "f"]
    rank = [0.28591, 0.42682, 0.35912, 0.21237, 0.60619, 0.47078]
    dst, de_rank = unwind(rank, src)
    assert dst == ["d", "a", "c", "b", "f", "e"]
