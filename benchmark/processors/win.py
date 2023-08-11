import itertools
import math
import time
from typing import Union

import jsonlines
import numpy as np
import trueskill
from prompt_toolkit import HTML
from prompt_toolkit import print_formatted_text as print
from prompt_toolkit.shortcuts import ProgressBar
from sklearn.model_selection import train_test_split

from openskill.models import (
    BradleyTerryFull,
    BradleyTerryPart,
    PlackettLuce,
    ThurstoneMostellerFull,
    ThurstoneMostellerPart,
)


def win_probability(team1, team2):
    delta_mu = sum(r.mu for r in team1) - sum(r.mu for r in team2)
    sum_sigma = sum(r.sigma**2 for r in itertools.chain(team1, team2))
    size = len(team1) + len(team2)
    denom = math.sqrt(size * (trueskill.BETA * trueskill.BETA) + sum_sigma)
    ts = trueskill.global_env()
    return ts.cdf(delta_mu / denom)


class Win:
    def __init__(
        self,
        path,
        seed: int,
        minimum_matches: int,
        model: Union[
            BradleyTerryFull,
            BradleyTerryPart,
            PlackettLuce,
            ThurstoneMostellerFull,
            ThurstoneMostellerPart,
        ] = PlackettLuce,
    ):
        self.data = list(jsonlines.open(path).iter())
        self.seed = seed
        self.minimum_matches = minimum_matches
        self.model = model

        # Counters
        self.match_count = {}
        self.available_matches = 0
        self.valid_matches = 0
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
                    self.valid_matches += 1

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
                f"Available Matches:  <style fg='Yellow'>{self.available_matches}</style>"
            )
        )
        print(HTML(f"Valid Matches:  <style fg='Yellow'>{self.valid_matches}</style>"))
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
        print(HTML(f"Mean Matches: <style fg='Yellow'>{mean: .2f}</style>"))
        print("-" * 40)
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

    def valid_test(self, match):
        teams: dict = match.get("teams")
        blue_team: dict = teams.get("blue")
        red_team: dict = teams.get("red")

        for player in blue_team:
            if player not in self.openskill_players:
                return False

        for player in red_team:
            if player not in self.openskill_players:
                return False

        return True

    def count(self, match):
        teams: dict = match.get("teams")
        blue_team: dict = teams.get("blue")
        red_team: dict = teams.get("red")

        for player in blue_team:
            self.match_count[player] = self.match_count.get(player, 0) + 1

        for player in red_team:
            self.match_count[player] = self.match_count.get(player, 0) + 1

    def has_sufficient_history(self, match):
        teams: dict = match.get("teams")
        blue_team: dict = teams.get("blue")
        red_team: dict = teams.get("red")

        for player in blue_team:
            if self.match_count[player] < self.minimum_matches:
                return False

        for player in red_team:
            if self.match_count[player] < self.minimum_matches:
                return False

        self.available_matches += 1
        return True

    def process_openskill(self, match):
        result = match.get("result")
        won = True if result == "WIN" else False

        teams: dict = match.get("teams")
        blue_team: dict = teams.get("blue")
        red_team: dict = teams.get("red")

        os_blue_players = {}
        os_red_players = {}

        m = self.model()
        r = m.rating

        for player in blue_team:
            os_blue_players[player] = r()

        for player in red_team:
            os_red_players[player] = r()

        if won:
            blue_team_result, red_team_result = m.rate(
                [list(os_blue_players.values()), list(os_red_players.values())],
                ranks=[0, 1],
            )
        else:
            red_team_result, blue_team_result = m.rate(
                [list(os_red_players.values()), list(os_blue_players.values())],
                ranks=[0, 1],
            )

        os_blue_players = dict(zip(os_blue_players, blue_team_result))
        os_red_players = dict(zip(os_red_players, red_team_result))

        self.openskill_players.update(os_blue_players)
        self.openskill_players.update(os_red_players)

    def process_trueskill(self, match):
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

        self.trueskill_players.update(ts_blue_players)
        self.trueskill_players.update(ts_red_players)

    def predict_openskill(self, match):
        result = match.get("result")
        won = True if result == "WIN" else False

        teams: dict = match.get("teams")
        blue_team: dict = teams.get("blue")
        red_team: dict = teams.get("red")

        os_blue_players = {}
        os_red_players = {}

        for player in blue_team:
            os_blue_players[player] = self.openskill_players[player]

        for player in red_team:
            os_red_players[player] = self.openskill_players[player]

        m = self.model()

        blue_win_probability, red_win_probability = m.predict_win(
            [list(os_blue_players.values()), list(os_red_players.values())]
        )
        if (blue_win_probability > red_win_probability) == won:
            self.openskill_correct_predictions += 1
        else:
            self.openskill_incorrect_predictions += 1

    def predict_trueskill(self, match):
        result = match.get("result")
        won = True if result == "WIN" else False

        teams: dict = match.get("teams")
        blue_team: dict = teams.get("blue")
        red_team: dict = teams.get("red")

        ts_blue_players = {}
        ts_red_players = {}

        for player in blue_team:
            ts_blue_players[player] = self.trueskill_players[player]

        for player in red_team:
            ts_red_players[player] = self.trueskill_players[player]

        blue_win_probability = win_probability(
            list(ts_blue_players.values()), list(ts_red_players.values())
        )
        red_win_probability = abs(1 - blue_win_probability)
        if (blue_win_probability > red_win_probability) == won:
            self.trueskill_correct_predictions += 1
        else:
            self.trueskill_incorrect_predictions += 1
