import math
from itertools import zip_longest
from typing import List, Optional, Tuple

from openskill.constants import Constants


def score(q, i) -> float:
    if q < i:
        return 0.0

    if q > i:
        return 1.0

    return 0.5


def rankings(teams, rank: Optional[List[int]] = None):
    if rank:
        team_scores = []
        for i, _ in enumerate(teams):
            if isinstance(rank[i], int):
                team_scores.append(rank[i])
            else:
                team_scores.append(i)
    else:
        team_scores = [i for i, _ in enumerate(teams)]

    out_rank = {}
    s = 0
    for index, value in enumerate(team_scores):
        if index > 0:
            if team_scores[index - 1] < team_scores[index]:
                s = index
        out_rank[index] = s
    return list(out_rank.values())


def ladder_pairs(ranks: List[int]):
    left = [None]
    left.extend(ranks[:-1])
    right = list(ranks[1:])
    right.append(None)
    zipped_lr = zip_longest(left, right)
    result = []
    for _left, _right in zipped_lr:
        if _left and _right:
            result.append([_left, _right])
        elif _left and not _right:
            result.append([_left])
        elif not _left and _right:
            result.append([_right])
        else:
            result.append([])
    return result


def util_c(team_ratings, **options):
    constants = Constants(**options)
    beta_squared = constants.BETA_SQUARED
    collective_team_sigma = 0
    for team in team_ratings:
        _team_mu, team_sigma_squared, _team, _rank = team
        collective_team_sigma += team_sigma_squared + beta_squared
    return math.sqrt(collective_team_sigma)


def util_sum_q(team_ratings, c):
    sum_q = {}
    for i, i_team in enumerate(team_ratings):
        team_i_mu, _team_i_sigma_squared, _i_team, i_rank = i_team
        temp = math.exp(team_i_mu / c)
        for q, q_team in enumerate(team_ratings):
            _team_q_mu, _team_q_sigma_squared, _q_team, q_rank = q_team
            if i_rank >= q_rank:
                if q in sum_q:
                    sum_q[q] += temp
                else:
                    sum_q[q] = temp
    return list(sum_q.values())


def util_a(team_ratings):
    result = list(
        map(
            lambda i: len(list(filter(lambda q: i[3] == q[3], team_ratings))),
            team_ratings,
        )
    )
    return result


def gamma(**options):
    if "gamma" in options:
        return options["gamma"]
    else:
        return (
            lambda c, _k, _mu, sigma_squared, _team, _q_rank: math.sqrt(sigma_squared)
            / c
        )


def transpose(xs):
    return [list(map(lambda r: r[i], xs)) for i, _ in enumerate(xs[0])]


def unwind(ranks, teams) -> Tuple[List, List[int]]:
    if not ranks or not teams:
        return None, None

    def sorter(teams):
        unsorted_list = transpose([[ranks[i], [x, i]] for i, x in enumerate(teams)])
        sorted_list = [
            x
            for _, x in sorted(
                zip(unsorted_list[0], unsorted_list[1]), key=lambda pair: pair[0]
            )
        ]
        return [x for x, _ in sorted_list], [x for _, x in sorted_list]

    return sorter(teams) if isinstance(teams, list) else sorter
