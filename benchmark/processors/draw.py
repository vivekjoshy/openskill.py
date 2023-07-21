import itertools
import math
import time
from typing import Union

import numpy as np
import pandas
import trueskill
from prompt_toolkit import HTML
from prompt_toolkit import print_formatted_text as print
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


def result(match):
    if match["white_result"] == "win" and match["black_result"] == "checkmated":
        return "win"
    elif match["white_result"] == "checkmated" and match["black_result"] == "win":
        return "loss"
    elif match["white_result"] == "stalemate" and match["black_result"] == "stalemate":
        return "draw"
    else:
        return False


def win_probability(team1, team2):
    delta_mu = sum(r.mu for r in team1) - sum(r.mu for r in team2)
    sum_sigma = sum(r.sigma**2 for r in itertools.chain(team1, team2))
    size = len(team1) + len(team2)
    denom = math.sqrt(size * (trueskill.BETA * trueskill.BETA) + sum_sigma)
    ts = trueskill.global_env()
    return ts.cdf(delta_mu / denom)


class Draw:
    def __init__(
        self,
        path,
        seed: int,
        model: Union[
            BradleyTerryFull,
            BradleyTerryPart,
            PlackettLuce,
            ThurstoneMostellerFull,
            ThurstoneMostellerPart,
        ] = PlackettLuce,
    ):
        df = pandas.read_csv(path)

        self.data = []
        for match_index, row in df.iterrows():
            self.data.append(row)
        self.seed = seed
        self.model = model

        # Counters
        self.match_count = {}
        self.confident_matches = 0
        self.openskill_correct_predictions = 0
        self.openskill_incorrect_predictions = 0
        self.trueskill_correct_predictions = 0
        self.trueskill_incorrect_predictions = 0

        # Post Verification of Data
        self.verified_matches = []
        self.verified_test_set = []

        # Split Data
        self.training_set = []
        self.test_set = []

        # Ratings
        self.openskill_players = {}
        self.trueskill_players = {}

        # Time Spent
        self.openskill_time = None
        self.trueskill_time = None

    def process(self):
        title = HTML(f'<style fg="Red">Counting Matches</style>')
        with ProgressBar(title=title) as progress_bar:
            for match in progress_bar(self.data, total=len(self.data)):
                if self.consistent(match=match):
                    self.count(match=match)

        # Check if data has sufficient history.
        title = HTML(f'<style fg="Red">Verifying History</style>')
        with ProgressBar(title=title) as progress_bar:
            for match in progress_bar(self.data, total=len(self.data)):
                if self.consistent(match=match):
                    if self.has_sufficient_history(match=match):
                        self.verified_matches.append(match)

        # Split Data
        print(HTML(f'<style fg="Red">Splitting Data</style>'))
        self.training_set, self.test_set = train_test_split(
            self.verified_matches, test_size=0.33, random_state=self.seed
        )

        # Process OpenSkill Ratings
        title = HTML(
            f'Updating OpenSkill Ratings with <style fg="Green">{self.model.__name__}</style> Model:'
        )
        with ProgressBar(title=title) as progress_bar:
            os_process_time_start = time.time()
            for match in progress_bar(self.training_set, total=len(self.training_set)):
                self.process_openskill(match=match)
        os_process_time_stop = time.time()
        self.openskill_time = os_process_time_stop - os_process_time_start

        # Process TrueSkill Ratings
        title = HTML(
            f'Updating Ratings with <style fg="Green">TrueSkill</style> Model:'
        )
        with ProgressBar(title=title) as progress_bar:
            ts_process_time_start = time.time()
            for match in progress_bar(self.training_set, total=len(self.training_set)):
                self.process_trueskill(match=match)
        ts_process_time_stop = time.time()
        self.trueskill_time = ts_process_time_stop - ts_process_time_start

        # Process Test Set
        title = HTML(f'<style fg="Red">Processing Test Set</style>')
        with ProgressBar(title=title) as progress_bar:
            for match in progress_bar(self.test_set, total=len(self.test_set)):
                if self.valid_test(match=match):
                    self.verified_test_set.append(match)

        # Predict OpenSkill Matches
        title = HTML(f'<style fg="Blue">Predicting OpenSkill Matches:</style>')
        with ProgressBar(title=title) as progress_bar:
            for match in progress_bar(
                self.verified_test_set, total=len(self.verified_test_set)
            ):
                self.predict_openskill(match=match)

        # Predict TrueSkill Matches
        title = HTML(f'<style fg="Blue">Predicting TrueSkill Matches:</style>')
        with ProgressBar(title=title) as progress_bar:
            for match in progress_bar(
                self.verified_test_set, total=len(self.verified_test_set)
            ):
                self.predict_trueskill(match=match)

    def print_result(self):
        mean = float(np.array(list(self.match_count.values())).mean())
        print("-" * 40)
        print(
            HTML(
                f"Confident Matches:  <style fg='Yellow'>{self.confident_matches}</style>"
            )
        )
        print(
            HTML(
                f"Predictions Made with OpenSkill's <style fg='Green'><u>{self.model.__name__}</u></style> Model:"
            )
        )
        print(
            HTML(
                f"Correct: <style fg='Yellow'>{self.openskill_correct_predictions}</style> | "
                f"Incorrect: <style fg='Yellow'>{self.openskill_incorrect_predictions}</style>"
            )
        )
        openskill_accuracy = round(
            (
                self.openskill_correct_predictions
                / (
                    self.openskill_incorrect_predictions
                    + self.openskill_correct_predictions
                )
            )
            * 100,
            2,
        )
        print(
            HTML(
                f"Accuracy: <style fg='Yellow'>"
                f"{openskill_accuracy: .2f}%"
                f"</style>"
            )
        )
        print(
            HTML(
                f"Process Duration: <style fg='Yellow'>{self.openskill_time: .2f}</style>"
            )
        )
        print("-" * 40)
        print(
            HTML(
                f"Predictions Made with <style fg='Green'><u>TrueSkill</u></style> Model:"
            )
        )
        print(
            HTML(
                f"Correct: <style fg='Yellow'>{self.trueskill_correct_predictions}</style> | "
                f"Incorrect: <style fg='Yellow'>{self.trueskill_incorrect_predictions}</style>"
            )
        )
        trueskill_accuracy = round(
            (
                self.trueskill_correct_predictions
                / (
                    self.trueskill_incorrect_predictions
                    + self.trueskill_correct_predictions
                )
            )
            * 100,
            2,
        )
        print(
            HTML(
                f"Accuracy: <style fg='Yellow'>"
                f"{trueskill_accuracy: .2f}%"
                f"</style>"
            )
        )
        print(
            HTML(
                f"Process Duration: <style fg='Yellow'>{self.trueskill_time: .2f}</style>"
            )
        )
        print("-" * 40)
        print(HTML(f"Mean Matches: <style fg='Yellow'>{mean: .2f}</style>"))
        speedup = (
            (self.trueskill_time - self.openskill_time) / self.openskill_time
        ) * 100
        print(HTML(f"Speedup (%): <style fg='Yellow'>{speedup: .2f}</style>"))
        accuracy_bump = (
            (openskill_accuracy - trueskill_accuracy) / trueskill_accuracy
        ) * 100
        print(
            HTML(f"Accuracy Bump (%): <style fg='Yellow'>{accuracy_bump: .2f}</style>")
        )

    def consistent(self, match):
        if match["white_result"] == "win" and match["black_result"] == "checkmated":
            return True
        elif match["white_result"] == "checkmated" and match["black_result"] == "win":
            return True
        elif (
            match["white_result"] == "stalemate"
            and match["black_result"] == "stalemate"
        ):
            return True
        else:
            return False

    def valid_test(self, match):
        white_player: dict = match["white_username"]
        black_player: dict = match["black_username"]

        if not (white_player in self.trueskill_players):
            return False

        if not (black_player in self.openskill_players):
            return False

        return True

    def count(self, match):
        white_player: dict = match["white_username"]
        black_player: dict = match["black_username"]

        self.match_count[white_player] = self.match_count.get(white_player, 0) + 1
        self.match_count[black_player] = self.match_count.get(black_player, 0) + 1

    def has_sufficient_history(self, match):
        white_player: dict = match["white_username"]
        black_player: dict = match["black_username"]

        if self.match_count[white_player] < 2:
            return False

        if self.match_count[black_player] < 2:
            return False

        self.confident_matches += 1
        return True

    def process_openskill(self, match):
        result_status = result(match)

        white_player: dict = match["white_username"]
        black_player: dict = match["black_username"]

        m = self.model()
        r = m.rating

        os_white_player = r()
        os_black_player = r()

        if result_status == "win":
            white_player_result, black_player_result = m.rate(
                [[os_white_player], [os_black_player]]
            )
        elif result_status == "loss":
            black_player_result, white_player_result = m.rate(
                [[os_black_player], [os_white_player]]
            )
        else:
            white_player_result, black_player_result = m.rate(
                [[os_white_player], [os_black_player]], ranks=[1, 1]
            )

        os_white_players = dict(zip([white_player], white_player_result))
        os_black_players = dict(zip([black_player], black_player_result))

        self.openskill_players.update(os_white_players)
        self.openskill_players.update(os_black_players)

    def process_trueskill(self, match):
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

        self.trueskill_players.update(ts_white_players)
        self.trueskill_players.update(ts_black_players)

    def predict_openskill(self, match):
        result_status = result(match)
        if result_status in ["win", "loss"]:
            draw = False
        else:
            draw = True

        white_player: dict = match["white_username"]
        black_player: dict = match["black_username"]

        os_white_player = self.openskill_players[white_player]
        os_black_player = self.openskill_players[black_player]

        m = self.model()

        white_win_probability, black_win_probability = m.predict_win(
            [[os_white_player], [os_black_player]]
        )

        draw_probability = m.predict_draw([[os_white_player], [os_black_player]])

        if draw_probability > (white_win_probability + black_win_probability):
            current_status = True
            if current_status == draw:
                self.openskill_correct_predictions += 1
            else:
                self.openskill_incorrect_predictions += 1
        else:
            current_status = False
            if current_status == draw:
                self.openskill_correct_predictions += 1
            else:
                self.openskill_incorrect_predictions += 1

    def predict_trueskill(self, match):
        result_status = result(match)
        if result_status in ["win", "loss"]:
            draw = False
        else:
            draw = True

        white_player: dict = match["white_username"]
        black_player: dict = match["black_username"]

        ts_white_player = self.trueskill_players[white_player]
        ts_black_player = self.trueskill_players[black_player]

        white_win_probability = win_probability([ts_white_player], [ts_black_player])
        black_win_probability = abs(1 - white_win_probability)
        draw_probability = trueskill.quality([[ts_white_player], [ts_black_player]])

        if draw_probability > (white_win_probability + black_win_probability):
            current_status = True
            if current_status == draw:
                self.trueskill_correct_predictions += 1
            else:
                self.trueskill_incorrect_predictions += 1
        else:
            current_status = False
            if current_status == draw:
                self.trueskill_correct_predictions += 1
            else:
                self.trueskill_incorrect_predictions += 1
