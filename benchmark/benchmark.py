#!/usr/bin/env python
"""
Rating System Benchmark

A standalone script to benchmark multiple OpenSkill rating systems with different margin values:
- PlackettLuce (baseline)
- ThurstoneMostellerPart
- ThurstoneMostellerFull
- BradleyTerryFull
- BradleyTerryPart

Each system is tested with margin=0.0 and margin=2.0 to evaluate the impact on prediction accuracy.
"""

import gc
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union, cast

import jsonlines
import numpy as np
import rich
from rich.console import Console
from rich.progress import track
from rich.table import Table
from sklearn.model_selection import KFold

from openskill.models import (
    BradleyTerryFull,
    BradleyTerryPart,
    PlackettLuce,
    ThurstoneMostellerFull,
    ThurstoneMostellerPart,
)


class RatingSystemBenchmark:
    """
    A benchmark utility for comparing multiple OpenSkill rating systems:
    - PlackettLuce (baseline)
    - ThurstoneMostellerPart
    - ThurstoneMostellerFull
    - BradleyTerryFull
    - BradleyTerryPart

    Each system is tested with different margin values to evaluate the impact.
    """

    def __init__(
        self,
        data_path: Path,
        n_splits: int = 3,
        minimum_matches: int = 0,
        random_state: int = 7,
    ):
        """
        Initialize the benchmark with configuration settings.

        :param data_path: Path to the match data file (jsonl format)
        :param n_splits: Number of splits for cross-validation
        :param minimum_matches: Minimum number of matches a player must have to be included
        :param random_state: Random seed for reproducibility
        """
        self.data_path = data_path
        self.n_splits = n_splits
        self.minimum_matches = minimum_matches
        self.random_state = random_state
        self.console = Console()
        self.verified_matches: List[Dict[str, Any]] = []

        # Define the models to test
        self.models = {
            "PlackettLuce": PlackettLuce,
            "ThurstoneMostellerPart": ThurstoneMostellerPart,
            "ThurstoneMostellerFull": ThurstoneMostellerFull,
            "BradleyTerryFull": BradleyTerryFull,
            "BradleyTerryPart": BradleyTerryPart,
        }

        # Define margins to test
        self.margins = [0.0, 2.0]

    def load_data(self) -> None:
        """
        Load and process match data from the specified path.
        Filters matches based on minimum match count requirements.
        """
        with self.console.status("[bold green]Loading Data:"):
            data = list(jsonlines.open(self.data_path).iter())
            match_count: defaultdict[str, int] = defaultdict(int)

            # Count matches per player
            for match in data:
                if not isinstance(match, dict):
                    continue

                result = match.get("result")
                if result not in ["WIN", "LOSS"]:
                    continue

                teams = match.get("teams")
                if not isinstance(teams, dict):
                    continue

                if list(teams.keys()) != ["blue", "red"]:
                    continue

                blue_team = teams.get("blue")
                red_team = teams.get("red")
                if not isinstance(blue_team, list) or not isinstance(red_team, list):
                    continue

                compositions = match.get("compositions")
                if not compositions:
                    continue

                for player in blue_team + red_team:
                    match_count[str(player)] += 1

            # Filter valid matches
            self.verified_matches = []
            for match in track(data, description="Processing Matches"):
                if not self._is_valid_match(match):
                    continue

                # Check if all players have minimum matches
                blue_team, red_team = self._extract_teams(match)
                if all(
                    match_count[str(p)] >= self.minimum_matches
                    for p in blue_team + red_team
                ):
                    self.verified_matches.append(match)

        rich.print(
            f"[bold green]Processed {len(self.verified_matches)} valid matches[/bold green]"
        )

    def _is_valid_match(self, match: Any) -> bool:
        """
        Check if a match object is valid for processing.

        :param match: Match data
        :return: True if valid, False otherwise
        """
        if not isinstance(match, dict):
            return False

        result = match.get("result")
        if result not in ["WIN", "LOSS"]:
            return False

        teams = match.get("teams")
        if not isinstance(teams, dict):
            return False

        if list(teams.keys()) != ["blue", "red"]:
            return False

        blue_team = teams.get("blue")
        red_team = teams.get("red")
        if not isinstance(blue_team, list) or not isinstance(red_team, list):
            return False

        compositions = match.get("compositions")
        if not compositions:
            return False

        return True

    def _extract_teams(self, match: Dict[str, Any]) -> Tuple[List[Any], List[Any]]:
        """
        Extract team data from a match.

        :param match: Match dictionary
        :return: Tuple of (blue_team, red_team)
        """
        teams = match.get("teams")
        if isinstance(teams, dict):
            blue_team = teams.get("blue", [])
            red_team = teams.get("red", [])
            if isinstance(blue_team, list) and isinstance(red_team, list):
                return blue_team, red_team
        return [], []

    def train_model(
        self, model_class: Any, matches: List[Dict[str, Any]], margin: float
    ) -> Tuple[Dict[str, Any], Any]:
        """
        Train a rating system model on the provided matches.

        :param model_class: The rating system class to use
        :param matches: List of match dictionaries
        :param margin: Margin value to use for the model
        :return: Tuple of (player ratings dictionary, model)
        """
        players: Dict[str, Any] = {}
        model = model_class(margin=margin)

        for match in matches:
            if not self._is_valid_match(match):
                continue

            result = match.get("result")
            won = result == "WIN"
            blue_team, red_team = self._extract_teams(match)

            compositions = match.get("compositions")
            blue_score = float(compositions.get("blue_won_fights"))
            red_score = float(compositions.get("red_won_fights"))

            blue_players: Dict[str, Any] = {}
            red_players: Dict[str, Any] = {}

            # Initialize ratings
            r = model.rating
            for player in blue_team:
                blue_players[str(player)] = players.setdefault(str(player), r())
            for player in red_team:
                red_players[str(player)] = players.setdefault(str(player), r())

            if won:
                blue_result, red_result = model.rate(
                    [list(blue_players.values()), list(red_players.values())],
                    scores=[blue_score, red_score],
                )
            else:
                red_result, blue_result = model.rate(
                    [list(red_players.values()), list(blue_players.values())],
                    scores=[red_score, blue_score],
                )

            # Update player ratings
            players.update(dict(zip(blue_players.keys(), blue_result)))
            players.update(dict(zip(red_players.keys(), red_result)))

        return players, model

    def evaluate_model(
        self,
        model: Any,
        players: Dict[str, Any],
        matches: List[Dict[str, Any]],
    ) -> Tuple[int, int]:
        """
        Evaluate model predictions on test matches.

        :param model: Trained model
        :param players: Dictionary of player ratings
        :param matches: List of match dictionaries to evaluate on
        :return: Tuple of (correct predictions, total predictions)
        """
        correct = 0
        total = 0

        for match in matches:
            if not self._is_valid_match(match):
                continue

            result = match.get("result")
            won = result == "WIN"
            blue_team, red_team = self._extract_teams(match)

            # Skip matches with players not in training set
            if any(str(player) not in players for player in blue_team + red_team):
                continue

            blue_ratings = [players[str(p)] for p in blue_team]
            red_ratings = [players[str(p)] for p in red_team]

            # Get win probabilities
            win_probs = model.predict_win([blue_ratings, red_ratings])
            predicted_blue_wins = win_probs[0] > win_probs[1]

            if predicted_blue_wins == won:
                correct += 1
            total += 1

        return correct, total

    def run_benchmark(
        self,
    ) -> Dict[str, Dict[float, Dict[str, List[Union[int, float]]]]]:
        """
        Run the benchmark using cross-validation to compare all rating systems
        with different margin values.

        :return: Dictionary of benchmark results
        """
        if not self.verified_matches:
            self.load_data()

        # Initialize K-Fold
        kf = KFold(n_splits=self.n_splits, shuffle=True, random_state=self.random_state)

        # Results storage - model_name -> margin -> metrics
        results: Dict[str, Dict[float, Dict[str, List[Union[int, float]]]]] = {}
        for model_name in self.models:
            results[model_name] = {}
            for margin in self.margins:
                results[model_name][margin] = {"correct": [], "total": [], "time": []}

        # Perform cross validation
        for fold, (train_idx, test_idx) in enumerate(
            kf.split(self.verified_matches), 1
        ):
            train_matches = [self.verified_matches[i] for i in train_idx]
            test_matches = [self.verified_matches[i] for i in test_idx]

            rich.print(f"\n[bold cyan]Fold {fold}/{self.n_splits}[/bold cyan]")

            # Train and evaluate each model with each margin
            for model_name, model_class in self.models.items():
                for margin in self.margins:
                    with self.console.status(
                        f"[bold green]Training {model_name} (margin={margin}):"
                    ):
                        start_time = time.time()
                        players, model = self.train_model(
                            model_class, train_matches, margin
                        )
                        train_time = time.time() - start_time

                        correct, total = self.evaluate_model(
                            model, players, test_matches
                        )

                    # Store results
                    results[model_name][margin]["correct"].append(correct)
                    results[model_name][margin]["total"].append(total)
                    results[model_name][margin]["time"].append(train_time)

                    # Print interim results
                    accuracy = (correct / total) * 100 if total > 0 else 0
                    rich.print(
                        f"{model_name} (margin={margin}): {accuracy:.2f}% accuracy, {train_time:.2f}s"
                    )

                    # Clean up memory
                    del players, model
                    _ = gc.collect()

        return results

    @staticmethod
    def calculate_metrics(
        results: Dict[str, List[Union[int, float]]],
    ) -> Tuple[int, int, float, float, float]:
        """
        Calculate aggregate metrics from benchmark results.

        :param results: Dictionary of benchmark results
        :return: Tuple of (correct, total, accuracy, avg_time, std_acc)
        """
        correct_list = cast(List[int], results["correct"])
        total_list = cast(List[int], results["total"])
        time_list = cast(List[float], results["time"])

        correct = np.sum(correct_list)
        total = np.sum(total_list)
        accuracy = (correct / total) * 100 if total > 0 else 0
        avg_time = np.mean(time_list)
        std_acc = (
            np.std([c / t * 100 for c, t in zip(correct_list, total_list) if t > 0])
            if total > 0
            else 0
        )
        return (
            int(correct),
            int(total),
            float(accuracy),
            float(avg_time),
            float(std_acc),
        )

    def display_results(
        self, results: Dict[str, Dict[float, Dict[str, List[Union[int, float]]]]]
    ) -> Table:
        """
        Create and display a table of benchmark results comparing different margin values.

        :param results: Dictionary of benchmark results
        :return: Rich Table object with formatted results
        """
        # Create results table for margin comparison
        table = Table(title="Rating System Benchmark Results - Margin Comparison")
        table.add_column("Model", style="cyan")
        table.add_column("Margin", style="blue")
        table.add_column("Accuracy", style="magenta")
        table.add_column("Predictions", style="green")
        table.add_column("Avg Time (s)", style="yellow")

        # Add a separate table for margin difference analysis
        diff_table = Table(title="Margin Impact Analysis (2.0 vs 0.0)")
        diff_table.add_column("Model", style="cyan")
        diff_table.add_column("Accuracy Difference", style="magenta")
        diff_table.add_column("Speed Difference", style="yellow")

        # Calculate and add rows for each model and margin
        for model_name in self.models:
            metrics_by_margin = {}

            for margin in self.margins:
                metrics = self.calculate_metrics(results[model_name][margin])
                metrics_by_margin[margin] = metrics

                table.add_row(
                    model_name,
                    f"{margin:.1f}",
                    f"{metrics[2]:.2f}% ± {metrics[4]:.2f}%",
                    f"{metrics[0]}/{metrics[1]}",
                    f"{metrics[3]:.2f}",
                )

            # Calculate the difference between margin=2.0 and margin=0.0
            if 0.0 in metrics_by_margin and 2.0 in metrics_by_margin:
                m0 = metrics_by_margin[0.0]
                m2 = metrics_by_margin[2.0]

                acc_diff = m2[2] - m0[2]
                time_diff = (m2[3] / m0[3] - 1.0) * 100

                diff_table.add_row(
                    model_name,
                    f"{acc_diff:.2f}% {'better' if acc_diff > 0 else 'worse'}",
                    f"{abs(time_diff):.2f}% {'slower' if time_diff > 0 else 'faster'}",
                )

        # Print tables
        self.console.print(table)
        self.console.print("\n")
        self.console.print(diff_table)

        # Clean up memory
        _ = gc.collect()

        return table


def download_dataset(data_directory: Path) -> Path:
    """
    Download the dataset if it doesn't exist.

    :param data_directory: Directory to save the data
    :return: Path to the dataset
    """
    # Create data directory if it doesn't exist
    data_directory.mkdir(exist_ok=True)

    # Check if file already exists
    file_path = data_directory / "overwatch.jsonl"
    if file_path.exists():
        print(f"Dataset Already Exists: {file_path}")
        return file_path

    from pooch import DOIDownloader

    downloader = DOIDownloader(progressbar=True)
    downloader(
        url="doi:10.5281/zenodo.10359600/overwatch.jsonl",
        output_file=file_path,
        pooch=None,
    )
    print(f"Dataset Downloaded: {file_path}")

    return file_path


if __name__ == "__main__":
    # Set up directories
    working_directory = Path.cwd()
    data_directory = Path(working_directory / "data")

    # Download dataset if needed
    data_path = download_dataset(data_directory)

    # Configure and run benchmark
    console = Console()

    with console.status("[bold green]Initializing Benchmark:"):
        benchmark = RatingSystemBenchmark(
            data_path=data_path,
            n_splits=3,
            minimum_matches=0,
            random_state=7,
        )

    # Run benchmark
    console.print("[bold]Running Benchmark:[/bold]")
    results = benchmark.run_benchmark()

    # Display results
    console.print("\n[bold]Benchmark Results:[/bold]")
    table = benchmark.display_results(results)
