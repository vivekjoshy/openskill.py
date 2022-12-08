from processors import Draw, Rank, Win
from prompt_toolkit import HTML
from prompt_toolkit import print_formatted_text as print
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import ValidationError, Validator

from benchmark.processors import Competition
from openskill.models import (
    BradleyTerryFull,
    BradleyTerryPart,
    PlackettLuce,
    ThurstoneMostellerFull,
    ThurstoneMostellerPart,
)


class NumberValidator(Validator):
    def validate(self, document):
        text = document.text

        if text and not text.isdigit():
            i = 0
            for i, c in enumerate(text):
                if not c.isdigit():
                    break

            raise ValidationError(
                message="This input contains non-numeric characters", cursor_position=i
            )


models = [
    BradleyTerryFull,
    BradleyTerryPart,
    PlackettLuce,
    ThurstoneMostellerFull,
    ThurstoneMostellerPart,
]
model_names = {m.__name__: m for m in models}
model_completer = WordCompleter(list(model_names.keys()))

benchmark_types = [Win, Draw, Rank]
benchmark_type_names = {_.__name__: _ for _ in benchmark_types}
benchmark_types_completer = WordCompleter(list(benchmark_type_names.keys()))


input_model = prompt("Enter Model: ", completer=model_completer)
input_benchmark_type = prompt(
    "Benchmark Processor: ", completer=benchmark_types_completer
)
input_seed = int(prompt("Enter Random Seed: ", validator=NumberValidator()))

model = None
if input_model in model_names.keys():
    model = model_names[input_model]
else:
    print(HTML("<style fg='Red'>Model Not Found</style>"))
    quit()

if input_benchmark_type in benchmark_type_names.keys() and model:
    if input_benchmark_type == "Win":
        win_processor = Win(path="data/overwatch.jsonl", seed=input_seed, model=model)
        win_processor.process()
        win_processor.print_result()
    elif input_benchmark_type == "Draw":
        draw_processor = Draw(path="data/chess.csv", seed=input_seed, model=model)
        draw_processor.process()
        draw_processor.print_result()
    elif input_benchmark_type == "Rank":
        rank_processor = Rank(path="data/overwatch.jsonl", seed=input_seed, model=model)
        rank_processor.process()
        rank_processor.print_result()
else:
    print(HTML("<style fg='Red'>Processor Not Found</style>"))
    quit()
