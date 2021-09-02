from openskill.util import ladder_pairs


def test_ladder_pairs():
    assert ladder_pairs([]) == [[]]
    assert ladder_pairs([1]) == [[]]
    assert ladder_pairs([1, 2]) == [[2], [1]]
    assert ladder_pairs([1, 2, 3]) == [[2], [1, 3], [2]]
    assert ladder_pairs([1, 2, 3, 4]) == [[2], [1, 3], [2, 4], [3]]
