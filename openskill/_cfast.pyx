# cython: boundscheck=False, wraparound=False, cdivision=True
"""Cython fast path for Ladder.rate().

Provides typed array access to the contiguous ``array.array('d')``
backing buffers, C-level ``sqrt``, and typed loop indices.
The ``model.rating()`` and ``model._compute()`` calls still go
through Python — this module optimises everything *around* them.
"""

from cpython cimport array
from libc.math cimport sqrt

import array

from openskill.batch import _FastRating


def cy_rate_game(
    object model,
    list team_id_lists,
    dict entity_to_idx,
    array.array mus,
    array.array sigmas,
    double tau_sq,
    bint limit_sigma,
    object ranks_in,
    object scores_in,
    object weights_in,
):
    """Rate a single game with typed array access.

    Parameters mirror :meth:`Ladder._rate_py` but operate on the raw
    ``array.array`` buffers via C double pointers.
    """
    cdef double* mu_data = mus.data.as_doubles
    cdef double* sig_data = sigmas.data.as_doubles
    cdef int idx
    cdef double s, new_sigma, orig_sigma
    cdef int team_idx, player_idx, n, i

    # ── Build Rating objects with tau-applied sigma ──────────────
    team_objs = []
    team_indices = []

    for team_ids in team_id_lists:
        team = []
        indices = []
        for eid in team_ids:
            idx = <int>entity_to_idx[eid]
            s = sig_data[idx]
            team.append(_FastRating(mu_data[idx], sqrt(s * s + tau_sq)))
            indices.append(idx)
        team_objs.append(team)
        team_indices.append(indices)

    # ── Score → rank conversion ─────────────────────────────────
    cdef list ranks_list = list(ranks_in) if ranks_in is not None else None
    cdef list scores_list = list(scores_in) if scores_in is not None else None
    cdef list weight_lists = (
        [list(w) for w in weights_in] if weights_in is not None else None
    )

    if not ranks_list and scores_list:
        ranks_list = [<double>(-<double>sc) for sc in scores_list]
        ranks_list = model._calculate_rankings(team_objs, ranks_list)

    # ── Sort by rank (PlackettLuce requires rank-ordered input) ─
    if ranks_list is not None:
        n = len(ranks_list)
        order = sorted(range(n), key=lambda i: ranks_list[i])
        team_objs = [team_objs[i] for i in order]
        team_indices = [team_indices[i] for i in order]
        ranks_list = sorted(ranks_list)
        if scores_list is not None:
            scores_list = [scores_list[i] for i in order]
        if weight_lists is not None:
            weight_lists = [weight_lists[i] for i in order]

    # ── Call the model's compute (stays Python) ─────────────────
    result = model._compute(
        teams=team_objs,
        ranks=ranks_list,
        scores=scores_list,
        weights=weight_lists,
    )

    # ── Write back with typed pointer access ────────────────────
    for team_idx in range(len(result)):
        team_result = result[team_idx]
        indices = team_indices[team_idx]
        for player_idx in range(len(team_result)):
            player = team_result[player_idx]
            idx = <int>indices[player_idx]
            new_sigma = <double>player.sigma
            if limit_sigma:
                orig_sigma = sig_data[idx]
                if new_sigma > orig_sigma:
                    new_sigma = orig_sigma
            mu_data[idx] = <double>player.mu
            sig_data[idx] = new_sigma
