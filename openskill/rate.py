from openskill.models.plackett_luce import PlackettLuce
from openskill.util import unwind


def rate(teams, **options):
    if "rank" in options:
        rank = options["rank"]
    else:
        if "score" in options:
            rank = list(map(lambda points: -points, options["score"]))
            options["rank"] = rank
        else:
            rank = None

    tenet = None
    if rank:
        ordered_teams, tenet = unwind(rank, teams)
        teams = ordered_teams
        rank = sorted(rank)
        options["rank"] = rank

    if "model" in options:
        model = options["model"](teams, **options)
    else:
        model = PlackettLuce(teams, **options)

    if rank and tenet:
        result = model.calculate()
        result, old_tenet = unwind(tenet, result)
        return result
    else:
        return model.calculate()
