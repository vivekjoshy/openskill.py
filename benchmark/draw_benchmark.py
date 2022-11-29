import itertools
import math
import time
from typing import Union

import numpy as np
import pandas
import trueskill
from prompt_toolkit import HTML
from prompt_toolkit import print_formatted_text as print
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import ProgressBar
from sklearn.model_selection import train_test_split

import openskill
from openskill.models import (
    BradleyTerryFull,
    BradleyTerryPart,
    PlackettLuce,
    ThurstoneMostellerFull,
    ThurstoneMostellerPart,
)

# Stores
os_players = {}
ts_players = {}

match_count = {}

matches = []
training_set = {}
test_set = {}
valid_test_set_matches = []

# Counters
os_correct_predictions = 0
os_incorrect_predictions = 0
ts_correct_predictions = 0
ts_incorrect_predictions = 0
confident_matches = 0


print(HTML("<u><b>Benchmark Starting</b></u>"))


def data_verified(match) -> bool:
    if match["white_result"] == "win" and match["black_result"] == "checkmated":
        return True
    elif match["white_result"] == "checkmated" and match["black_result"] == "win":
        return True
    elif match["white_result"] == "stalemate" and match["black_result"] == "stalemate":
        return True
    else:
        return False


def result(match):
    if match["white_result"] == "win" and match["black_result"] == "checkmated":
        return "win"
    elif match["white_result"] == "checkmated" and match["black_result"] == "win":
        return "loss"
    elif match["white_result"] == "stalemate" and match["black_result"] == "stalemate":
        return "draw"
    else:
        return False


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
    result_status = result(match)

    white_player: dict = match["white_username"]
    black_player: dict = match["black_username"]

    os_white_player = openskill.Rating()
    os_black_player = openskill.Rating()

    if result_status == "win":
        white_player_result, black_player_result = openskill.rate(
            [[os_white_player], [os_black_player]], model=model
        )
    elif result_status == "loss":
        black_player_result, white_player_result = openskill.rate(
            [[os_black_player], [os_white_player]], model=model
        )
    else:
        white_player_result, black_player_result = openskill.rate(
            [[os_white_player], [os_black_player]], model=model, rank=[1, 1]
        )

    os_white_players = dict(zip([white_player], white_player_result))
    os_black_players = dict(zip([black_player], black_player_result))

    os_players.update(os_white_players)
    os_players.update(os_black_players)


def process_ts_match(match: dict):
    result_status = result(match)

    white_player: dict = match["white_username"]
    black_player: dict = match["black_username"]

    ts_white_player = trueskill.Rating()
    ts_black_player = trueskill.Rating()

    if result_status == "win":
        white_player_ratings, black_player_ratings = trueskill.rate(
            [[ts_white_player], [ts_black_player]],
        )
    else:
        black_player_ratings, white_player_ratings = trueskill.rate(
            [[ts_black_player], [ts_white_player]]
        )

    ts_white_players = dict(zip([white_player], white_player_ratings))
    ts_black_players = dict(zip([black_player], black_player_ratings))

    ts_players.update(ts_white_players)
    ts_players.update(ts_black_players)


def predict_os_match(match):
    result_status = result(match)
    if result_status in ["win", "loss"]:
        draw = False
    else:
        draw = True

    white_player: dict = match["white_username"]
    black_player: dict = match["black_username"]

    os_white_player = os_players[white_player]
    os_black_player = os_players[black_player]

    white_win_probability, black_win_probability = openskill.predict_win(
        [[os_white_player], [os_black_player]]
    )

    draw_probability = openskill.predict_draw([[os_white_player], [os_black_player]])

    global os_correct_predictions
    global os_incorrect_predictions

    if draw_probability > (white_win_probability + black_win_probability):
        current_status = True
        if current_status == draw:
            os_correct_predictions += 1
        else:
            os_incorrect_predictions += 1
    else:
        current_status = False
        if current_status == draw:
            os_correct_predictions += 1
        else:
            os_incorrect_predictions += 1


def win_probability(team1, team2):
    delta_mu = sum(r.mu for r in team1) - sum(r.mu for r in team2)
    sum_sigma = sum(r.sigma**2 for r in itertools.chain(team1, team2))
    size = len(team1) + len(team2)
    denom = math.sqrt(size * (trueskill.BETA * trueskill.BETA) + sum_sigma)
    ts = trueskill.global_env()
    return ts.cdf(delta_mu / denom)


def predict_ts_match(match: dict):
    result_status = result(match)
    if result_status in ["win", "loss"]:
        draw = False
    else:
        draw = True

    white_player: dict = match["white_username"]
    black_player: dict = match["black_username"]

    ts_white_player = ts_players[white_player]
    ts_black_player = ts_players[black_player]

    white_win_probability = win_probability([ts_white_player], [ts_black_player])
    black_win_probability = abs(1 - white_win_probability)
    draw_probability = trueskill.quality([[ts_white_player], [ts_black_player]])

    global ts_correct_predictions
    global ts_incorrect_predictions

    if draw_probability > (white_win_probability + black_win_probability):
        current_status = True
        if current_status == draw:
            ts_correct_predictions += 1
        else:
            ts_incorrect_predictions += 1
    else:
        current_status = False
        if current_status == draw:
            ts_correct_predictions += 1
        else:
            ts_incorrect_predictions += 1


def process_match(match):
    white_player: dict = match["white_username"]
    black_player: dict = match["black_username"]

    match_count[white_player] = match_count.get(white_player, 0) + 1
    match_count[black_player] = match_count.get(black_player, 0) + 1


def valid_test_set(match: dict):
    white_player: dict = match["white_username"]
    black_player: dict = match["black_username"]

    if white_player not in os_players:
        return False

    if black_player not in os_players:
        return False

    return True


def confident_in_match(match: dict) -> bool:
    white_player: dict = match["white_username"]
    black_player: dict = match["black_username"]

    global confident_matches
    if match_count[white_player] < 2:
        return False

    if match_count[black_player] < 2:
        return False

    confident_matches += 1
    return True


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
    print(HTML("<style fg='red'>Model Not Found</style>"))
    quit()

df = pandas.read_csv("chess.csv")

lines = []
for match_index, row in df.iterrows():
    lines.append(row)

title = HTML(f'<style fg="red">Processing Matches</style>')
with ProgressBar(title=title) as progress_bar:
    for line in progress_bar(lines, total=len(lines)):
        if data_verified(match=line):
            process_match(match=line)

# Measure Confidence
title = HTML(f'<style fg="red">Splitting Data</style>')
with ProgressBar(title=title) as progress_bar:
    for line in progress_bar(lines, total=len(lines)):
        if data_verified(match=line):
            if confident_in_match(match=line):
                matches.append(line)

# Split Data
training_set, test_set = train_test_split(matches, test_size=0.33, random_state=True)

# Process OpenSkill Ratings
title = HTML(f'Updating Ratings with <style fg="Green">{input_model}</style> Model:')
with ProgressBar(title=title) as progress_bar:
    os_process_time_start = time.time()
    for line in progress_bar(training_set, total=len(training_set)):
        process_os_match(match=line, model=models[index])
os_process_time_stop = time.time()
os_time = os_process_time_stop - os_process_time_start

# Process TrueSkill Ratings
title = HTML(f'Updating Ratings with <style fg="Green">TrueSkill</style> Model:')
with ProgressBar(title=title) as progress_bar:
    ts_process_time_start = time.time()
    for line in progress_bar(training_set, total=len(training_set)):
        process_ts_match(match=line)
ts_process_time_stop = time.time()
ts_time = ts_process_time_stop - ts_process_time_start

# Process Test Set
title = HTML(f'<style fg="red">Processing Test Set</style>')
with ProgressBar(title=title) as progress_bar:
    for line in progress_bar(test_set, total=len(test_set)):
        if valid_test_set(match=line):
            valid_test_set_matches.append(line)

# predict OpenSkill Matches
title = HTML(f'<style fg="blue">predicting OpenSkill Matches:</style>')
with ProgressBar(title=title) as progress_bar:
    for line in progress_bar(valid_test_set_matches, total=len(valid_test_set_matches)):
        predict_os_match(match=line)

# predict TrueSkill Matches
title = HTML(f'<style fg="blue">predicting TrueSkill Matches:</style>')
with ProgressBar(title=title) as progress_bar:
    for line in progress_bar(valid_test_set_matches, total=len(valid_test_set_matches)):
        predict_ts_match(match=line)

mean = float(np.array(list(match_count.values())).mean())

print(HTML(f"Confident Matches: <style fg='Yellow'>{confident_matches}</style>"))
print(
    HTML(
        f"predictions Made with OpenSkill's <style fg='Green'><u>{input_model}</u></style> Model:"
    )
)
print(
    HTML(
        f"Correct: <style fg='Yellow'>{os_correct_predictions}</style> | "
        f"Incorrect: <style fg='Yellow'>{os_incorrect_predictions}</style>"
    )
)
print(
    HTML(
        f"Accuracy: <style fg='Yellow'>"
        f"{round((os_correct_predictions/(os_incorrect_predictions + os_correct_predictions)) * 100, 2)}%"
        f"</style>"
    )
)
print(HTML(f"Process Duration: <style fg='Yellow'>{os_time}</style>"))
print("-" * 40)
print(HTML(f"predictions Made with <style fg='Green'><u>TrueSkill</u></style> Model:"))
print(
    HTML(
        f"Correct: <style fg='Yellow'>{ts_correct_predictions}</style> | "
        f"Incorrect: <style fg='Yellow'>{ts_incorrect_predictions}</style>"
    )
)
print(
    HTML(
        f"Accuracy: <style fg='Yellow'>"
        f"{round((ts_correct_predictions/(ts_incorrect_predictions + ts_correct_predictions)) * 100, 2)}%"
        f"</style>"
    )
)
print(HTML(f"Process Duration: <style fg='Yellow'>{ts_time}</style>"))
print(HTML(f"Mean Matches: <style fg='Yellow'>{mean}</style>"))
