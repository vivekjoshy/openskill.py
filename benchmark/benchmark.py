import itertools
import math
import time
from typing import Union

import jsonlines
import trueskill
from prompt_toolkit import print_formatted_text as print, HTML, prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import ProgressBar

import openskill
from openskill.models import (
    ThurstoneMostellerPart,
    ThurstoneMostellerFull,
    BradleyTerryFull,
    BradleyTerryPart,
    PlackettLuce,
)

# Stores
os_players = {}
ts_players = {}

# Counters
os_correct_predictions = 0
os_incorrect_predictions = 0
ts_correct_predictions = 0
ts_incorrect_predictions = 0


print(HTML("<u><b>Benchmark Starting</b></u>"))


def data_verified(match: dict) -> bool:
    result = match.get("result")
    if result not in ["WIN", "LOSS"]:
        return False

    teams: dict = match.get("teams")
    if list(teams.keys()) != ["blue", "red"]:
        return False

    blue_team: dict = teams.get("blue")
    red_team: dict = teams.get("red")

    if len(blue_team) < 1 and len(red_team) < 1:
        return False

    return True


def process_os_match(
    match: dict,
    model: Union[
        BradleyTerryFull,
        BradleyTerryPart,
        PlackettLuce,
        ThurstoneMostellerFull,
        ThurstoneMostellerPart,
    ] = PlackettLuce,
):
    result = match.get("result")
    won = True if result == "WIN" else False

    teams: dict = match.get("teams")
    blue_team: dict = teams.get("blue")
    red_team: dict = teams.get("red")

    os_blue_players = {}
    os_red_players = {}

    for player in blue_team:
        os_blue_players[player] = openskill.Rating()

    for player in red_team:
        os_red_players[player] = openskill.Rating()

    if won:
        blue_team_result, red_team_result = openskill.rate(
            [list(os_blue_players.values()), list(os_red_players.values())], model=model
        )
    else:
        red_team_result, blue_team_result = openskill.rate(
            [list(os_red_players.values()), list(os_blue_players.values())], model=model
        )

    blue_team_ratings = [openskill.create_rating(_) for _ in blue_team_result]
    red_team_ratings = [openskill.create_rating(_) for _ in red_team_result]

    os_blue_players = dict(zip(os_blue_players, blue_team_ratings))
    os_red_players = dict(zip(os_red_players, red_team_ratings))

    os_players.update(os_blue_players)
    os_players.update(os_red_players)


def process_ts_match(match: dict):
    result = match.get("result")
    won = True if result == "WIN" else False

    teams: dict = match.get("teams")
    blue_team: dict = teams.get("blue")
    red_team: dict = teams.get("red")

    ts_blue_players = {}
    ts_red_players = {}

    for player in blue_team:
        ts_blue_players[player] = trueskill.Rating()

    for player in red_team:
        ts_red_players[player] = trueskill.Rating()

    if won:
        blue_team_ratings, red_team_ratings = trueskill.rate(
            [list(ts_blue_players.values()), list(ts_red_players.values())],
        )
    else:
        red_team_ratings, blue_team_ratings = trueskill.rate(
            [list(ts_red_players.values()), list(ts_blue_players.values())]
        )

    ts_blue_players = dict(zip(ts_blue_players, blue_team_ratings))
    ts_red_players = dict(zip(ts_red_players, red_team_ratings))

    ts_players.update(ts_blue_players)
    ts_players.update(ts_red_players)



def predict_os_match(match: dict):
    result = match.get("result")
    won = True if result == "WIN" else False

    teams: dict = match.get("teams")
    blue_team: dict = teams.get("blue")
    red_team: dict = teams.get("red")

    os_blue_players = {}
    os_red_players = {}

    for player in blue_team:
        os_blue_players[player] = os_players[player]

    for player in red_team:
        os_red_players[player] = os_players[player]

    blue_win_probability, red_win_probability = openskill.predict_win(
        [list(os_blue_players.values()), list(os_red_players.values())]
    )
    if (blue_win_probability > red_win_probability) == won:
        global os_correct_predictions
        os_correct_predictions += 1
    else:
        global os_incorrect_predictions
        os_incorrect_predictions += 1


def win_probability(team1, team2):
    delta_mu = sum(r.mu for r in team1) - sum(r.mu for r in team2)
    sum_sigma = sum(r.sigma ** 2 for r in itertools.chain(team1, team2))
    size = len(team1) + len(team2)
    denom = math.sqrt(size * (trueskill.BETA * trueskill.BETA) + sum_sigma)
    ts = trueskill.global_env()
    return ts.cdf(delta_mu / denom)


def predict_ts_match(match: dict):
    result = match.get("result")
    won = True if result == "WIN" else False

    teams: dict = match.get("teams")
    blue_team: dict = teams.get("blue")
    red_team: dict = teams.get("red")

    ts_blue_players = {}
    ts_red_players = {}

    for player in blue_team:
        ts_blue_players[player] = ts_players[player]

    for player in red_team:
        ts_red_players[player] = os_players[player]

    blue_win_probability = win_probability(
        list(ts_blue_players.values()), list(ts_red_players.values())
    )
    red_win_probability = abs(1 - blue_win_probability)
    if (blue_win_probability > red_win_probability) == won:
        global ts_correct_predictions
        ts_correct_predictions += 1
    else:
        global ts_incorrect_predictions
        ts_incorrect_predictions += 1


models = [
    BradleyTerryFull,
    BradleyTerryPart,
    PlackettLuce,
    ThurstoneMostellerFull,
    ThurstoneMostellerPart,
]
model_names = [m.__name__ for m in models]
model_completer = WordCompleter(model_names)
input_model = prompt("Enter Model: ", completer=model_completer)
if input_model in model_names:
    index = model_names.index(input_model)
else:
    print(HTML("<style fg='Red'>Model Not Found</style>"))
    quit()
with jsonlines.open("v2_jsonl_teams.jsonl") as reader:
    lines = list(reader.iter())

    # Process OpenSkill Ratings
    title = HTML(f'Updating Ratings with <style fg="Green">{input_model}</style> Model')
    with ProgressBar(title=title) as progress_bar:
        os_process_time_start = time.time()
        for line in progress_bar(lines, total=len(lines)):
            if data_verified(match=line):
                process_os_match(match=line, model=models[index])
    os_process_time_stop = time.time()
    os_time = os_process_time_stop - os_process_time_start

    # Process TrueSkill Ratings
    title = HTML(f'Updating Ratings with <style fg="Green">TrueSkill</style> Model')
    with ProgressBar(title=title) as progress_bar:
        ts_process_time_start = time.time()
        for line in progress_bar(lines, total=len(lines)):
            if data_verified(match=line):
                process_ts_match(match=line)
    ts_process_time_stop = time.time()
    ts_time = ts_process_time_stop - ts_process_time_start

    # Predict OpenSkill Matches
    title = HTML(f'<style fg="Blue">Predicting OpenSkill Matches:</style>')
    with ProgressBar(title=title) as progress_bar:
        for line in progress_bar(lines, total=len(lines)):
            if data_verified(match=line):
                predict_os_match(match=line)

    # Predict TrueSkill Matches
    title = HTML(f'<style fg="Blue">Predicting TrueSkill Matches:</style>')
    with ProgressBar(title=title) as progress_bar:
        for line in progress_bar(lines, total=len(lines)):
            if data_verified(match=line):
                predict_ts_match(match=line)


print(HTML(f"Predictions Made with OpenSkill's <style fg='Green'><u>{input_model}</u></style> Model:"))
print(HTML(f"Correct: <style fg='Yellow'>{os_correct_predictions}</style> | "
           f"Incorrect: <style fg='Yellow'>{os_incorrect_predictions}</style>"))
print(
    HTML(
        f"Accuracy: <style fg='Yellow'>"
        f"{round((os_correct_predictions/(os_incorrect_predictions + os_correct_predictions)) * 100, 2)}%"
        f"</style>"
    )
)
print(HTML(f"Process Duration: <style fg='Yellow'>{os_time}</style>"))
print("-" * 40)
print(HTML(f"Predictions Made with <style fg='Green'><u>TrueSkill</u></style> Model:"))
print(HTML(f"Correct: <style fg='Yellow'>{ts_correct_predictions}</style> | "
           f"Incorrect: <style fg='Yellow'>{ts_incorrect_predictions}</style>"))
print(
    HTML(
        f"Accuracy: <style fg='Yellow'>"
        f"{round((ts_correct_predictions/(ts_incorrect_predictions + ts_correct_predictions)) * 100, 2)}%"
        f"</style>"
    )
)
print(HTML(f"Process Duration: <style fg='Yellow'>{ts_time}</style>"))
