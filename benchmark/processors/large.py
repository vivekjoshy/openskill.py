import time
from typing import Union

import numpy as np
import polars as pl
import rbo
import rich
from prompt_toolkit.styles import Style
from rich.progress import Progress
from rich.table import Table
from sklearn.model_selection import train_test_split

from openskill.models import (
    BradleyTerryFull,
    BradleyTerryPart,
    PlackettLuce,
    ThurstoneMostellerFull,
    ThurstoneMostellerPart,
)


class Large:
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
        self.seed = seed
        self.minimum_matches = minimum_matches
        self.model = model

        # Progress Bar Styles
        self.style = Style.from_dict(
            {
                "label": "bg:#ffff00 #000000",
                "percentage": "bg:#ffff00 #000000",
                "current": "#448844",
                "bar": "",
            }
        )

        # Data
        self.matches = {}
        self.verified_matches = []

        # Counters
        self.match_count = {}
        self.available_matches = 0
        self.valid_matches = 0
        self.openskill_correct_predictions = 0
        self.openskill_incorrect_predictions = 0
        self.rbo_scores = []

        # Post Verification of Data
        self.verified_matches = []
        self.verified_test_set = []

        # Split Data
        self.training_set = []
        self.test_set = []

        # Ratings
        self.openskill_players = {}

        # Time Spent
        self.openskill_time = None

        # Generate Match Data
        chunk_size = 10**5
        total_size = 13849287
        total_chunks = int(round(total_size / chunk_size))
        reader = pl.read_csv_batched(path, batch_size=chunk_size)
        batches = reader.next_batches(1)

        with Progress() as progress:
            loading_task = progress.add_task(
                description="[red]Processing Chunks:", total=total_chunks
            )
            chunk_task = progress.add_task(
                description="[red]Parsing and Transforming Data:", total=chunk_size
            )
            while batches:
                for chunk in batches:
                    progress.reset(chunk_task)
                    progress.update(chunk_task, total=len(chunk))
                    for raw_player in chunk.rows(named=True):
                        player = {
                            "name": raw_player["player_name"],
                            "assists": raw_player["player_assists"],
                            "kills": raw_player["player_kills"],
                        }
                        team = {
                            "id": raw_player["team_id"],
                            "match": raw_player["match_id"],
                            "rank": raw_player["team_placement"],
                            "size": raw_player["party_size"],
                            "players": {},
                        }
                        match = {
                            "id": raw_player["match_id"],
                            "size": raw_player["game_size"],
                            "teams": {},
                        }
                        match_id = match["id"]
                        team_id = team["id"]
                        player_name = player["name"]
                        if match_id in self.matches:
                            if team in self.matches[match_id]["teams"].values():
                                self.matches[match_id]["teams"][team_id]["players"][
                                    player_name
                                ] = player
                            else:
                                self.matches[match_id]["teams"][team_id] = team
                                self.matches[match_id]["teams"][team_id]["players"][
                                    player_name
                                ] = player
                        else:
                            self.matches[match_id] = match
                            if team in self.matches[match_id]["teams"].values():
                                self.matches[match_id]["teams"][team_id]["players"][
                                    player_name
                                ] = player
                            else:
                                self.matches[match_id]["teams"][team_id] = team
                                self.matches[match_id]["teams"][team_id]["players"][
                                    player_name
                                ] = player
                        progress.update(chunk_task, advance=1)
                    batches = reader.next_batches(1)
                    progress.update(loading_task, advance=1)

    def process(self):
        with Progress() as progress:
            counting_task = progress.add_task(
                description="[red]Counting Matches and Players:",
                total=len(self.matches),
            )
            for match_id, match in self.matches.items():
                self.count(match)
                if self.has_sufficient_history(match):
                    self.verified_matches.append(match)
                progress.update(counting_task, advance=1)

            history_task = progress.add_task(
                description="[red]Ensuring Sufficient Match History:",
                total=len(self.matches),
            )
            for match_id, match in self.matches.items():
                if self.has_sufficient_history(match):
                    self.verified_matches.append(match)
                progress.update(history_task, advance=1)

            # Split Data
            self.training_set, self.test_set = train_test_split(
                self.verified_matches, test_size=0.33, random_state=self.seed
            )

            # Process OpenSkill
            os_task = progress.add_task(
                description=f"Initializing OpenSkill Ratings with "
                f"[green]{self.model.__name__}[/green] Model:",
                total=len(self.training_set),
            )
            os_process_time_start = time.time()
            for match in self.training_set:
                self.process_openskill(match=match)
                progress.update(os_task, advance=1)
            os_process_time_stop = time.time()
            self.openskill_time = os_process_time_stop - os_process_time_start

            rate_task = progress.add_task(
                description=f"Updating OpenSkill Ratings with "
                f"[green]{self.model.__name__}[/green] Model:",
                total=len(self.training_set),
            )
            os_process_time_start = time.time()
            for match in self.training_set:
                self.rate_openskill(match=match)
                progress.update(rate_task, advance=1)
            os_process_time_stop = time.time()
            self.openskill_time += os_process_time_stop - os_process_time_start

            # Process Test Set
            test_task = progress.add_task(
                description=f"[red]Processing Test Set[/red]:",
                total=len(self.test_set),
            )
            for match in self.test_set:
                if self.valid_test(match):
                    self.verified_test_set.append(match)
                    self.valid_matches += 1
                progress.update(test_task, advance=1)

            # Predict OpenSkill
            predict_os_task = progress.add_task(
                description=f"[blue]Predicting Matches using OpenSkill[/blue]:",
                total=len(self.verified_test_set),
            )
            for match in self.verified_test_set:
                self.predict_openskill(match)
                progress.update(predict_os_task, advance=1)

    def print_result(self):
        mean = float(np.array(list(self.match_count.values())).mean())
        table = Table(title="Benchmark Results")
        table.add_column("Information", justify="right", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")

        table.add_row("Available Matches", f"{self.available_matches}")
        table.add_row("Valid Matches", f"{self.valid_matches}")

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

        table.add_row(
            f"{self.model.__name__} Accuracy",
            f"{self.openskill_correct_predictions}/"
            f"{self.openskill_incorrect_predictions} "
            f"[{openskill_accuracy: .2f}%]",
        )
        rbo_score = (sum(self.rbo_scores) / len(self.rbo_scores)) * 100
        table.add_row("Rank-Biased Overlap Score: ", f"{rbo_score: .2f}")
        table.add_row("Duration", f"{self.openskill_time: .2f}")
        rich.print(table)

    def count(self, match):
        teams = match["teams"]
        for team_id, team in teams.items():
            for player_name, player in team["players"].items():
                self.match_count[player_name] = self.match_count.get(player_name, 0) + 1

    def has_sufficient_history(self, match):
        teams = match["teams"]
        if len(teams) < 2:
            return False

        for (
            team_id,
            team,
        ) in teams.items():
            for player_name, player in team["players"].items():
                if self.match_count[player_name] < self.minimum_matches:
                    return False

        self.available_matches += 1
        return True

    def process_openskill(self, match):
        m = self.model()
        r = m.rating

        os_teams = []
        os_players = {}
        team_ranks = []
        for team_id, team in match["teams"].items():
            os_team = []
            for player_name, player in team["players"].items():
                os_player = r(name=player_name)
                os_team.append(os_player)
                os_players[player_name] = os_player
            os_teams.append(os_team)
            team_ranks.append(team["rank"])

        self.openskill_players.update(os_players)

    def rate_openskill(self, match):
        m = self.model()
        r = m.rating

        os_teams = []
        os_team_kills = []
        os_players = {}
        team_ranks = []
        for team_id, team in match["teams"].items():
            os_team = []
            os_players_kills = []
            for player_name, player in team["players"].items():
                os_player = self.openskill_players[player_name]
                os_team.append(os_player)
                os_players_kills.append(player["kills"])
                os_players[player_name] = os_player
            os_teams.append(os_team)
            os_team_kills.append(os_players_kills)
            team_ranks.append(team["rank"])

        os_teams = m.rate(teams=os_teams, ranks=team_ranks)

        for team in os_teams:
            for player in team:
                os_players[player.name] = player

        self.openskill_players.update(os_players)

    def valid_test(self, match):
        teams = match["teams"]
        for team_id, team in teams.items():
            for player_name, player in team["players"].items():
                if player_name not in self.openskill_players:
                    return False
        return True

    def predict_openskill(self, match):
        teams = match["teams"]
        os_teams = []
        for team_id, team in teams.items():
            os_team = []
            for player_name, player in team["players"].items():
                os_player = self.openskill_players[player_name]
                os_team.append(os_player)
            os_teams.append(os_team)

        m = self.model()

        actual_ranks = {}
        for team_id, team in teams.items():
            actual_ranks[team["rank"]] = []
            for player_name, player in team["players"].items():
                os_player = self.openskill_players[player_name]
                actual_ranks[team["rank"]].append(os_player)
        actual_ranks = dict(sorted(actual_ranks.items()))
        predictions = [_[0] for _ in m.predict_rank(os_teams)]
        expected_ranks = {_[0]: _[1] for _ in zip(predictions, os_teams)}

        actual_ranks = dict(
            sorted(
                actual_ranks.items(),
                key=lambda x: [*expected_ranks.values()].index(x[1]),
            )
        )

        ar_index = next(iter(actual_ranks))
        er_index = next(iter(expected_ranks))

        similarity = rbo.RankingSimilarity(
            list(actual_ranks.keys()), list(expected_ranks.keys())
        ).rbo_ext()
        self.rbo_scores.append(similarity)

        if actual_ranks[ar_index] == expected_ranks[er_index]:
            self.openskill_correct_predictions += 1
        else:
            self.openskill_incorrect_predictions += 1
