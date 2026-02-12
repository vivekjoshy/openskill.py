# Fast Bulk Rating

`Ladder` and `BatchProcessor` provide a high-performance path for processing
many games without the per-call overhead of `model.rate()`.  No extra
dependencies are required — the speedup comes from architectural changes, not
native code.

## Why it's faster

`model.rate()` does three expensive things on **every** call:

| Overhead             | Cost (13 500 games) | Needed? |
|----------------------|---------------------:|---------|
| `copy.deepcopy()`    | ~240 ms              | No — Ladder owns the arrays |
| `uuid.uuid4()` per Rating | ~170 ms (kernel syscall) | No — `_compute()` never reads `.id` |
| Input validation     | ~50 ms               | No — Ladder controls inputs |

`Ladder` and `BatchProcessor` skip all three.  Rating objects are replaced
with `_FastRating` — a minimal `__slots__` class with just `.mu`, `.sigma`,
and `.ordinal()`.  No UUID, no `__dict__`, no deepcopy.

## Install

### Base (pure Python, no extra dependencies)

```bash
pip install openskill
```

This gives you `Ladder`, `BatchProcessor`, and the full 5-7x speedup.  Nothing
else to install.

### With Cython (optional, ~10-15% additional gain)

```bash
pip install cython
cython openskill/_cfast.pyx -o _cfast.c
# Then build the extension in-place (adjust for your platform):
gcc -shared -fPIC -O2 \
    $(python -c "import sysconfig; print(sysconfig.get_config_var('CFLAGS'))") \
    -I$(python -c "import sysconfig; print(sysconfig.get_path('include'))") \
    _cfast.c \
    -o openskill/_cfast$(python -c "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))")
```

Cython is detected automatically at runtime.  If the compiled extension is
present, `Ladder` uses it; otherwise it falls back to the pure-Python path
transparently.  You can check which path is active:

```python
from openskill.ladder import _HAS_CYTHON
print(_HAS_CYTHON)  # True if Cython extension loaded
```

## Usage

### Ladder — stateful rating tracker

Best for online/streaming scenarios where games arrive over time.

```python
from openskill.ladder import Ladder
from openskill.models.weng_lin.plackett_luce import PlackettLuce

model = PlackettLuce()
ladder = Ladder(model)

# Register players (or let rate() auto-register them)
ladder.add("alice")
ladder.add("bob")

# Rate a single game: alice beat bob
ladder.rate(teams=[["alice"], ["bob"]])

# Check ratings via views (lightweight pointers into backing arrays)
view = ladder["alice"]
print(view.mu, view.sigma, view.ordinal())

# Rate a batch of games at once (dependency-aware wave scheduling)
games = [
    {"teams": [["alice"], ["charlie"]]},
    {"teams": [["bob"], ["dave"]]},      # independent — runs in same wave
    {"teams": [["alice"], ["bob"]]},      # depends on above — next wave
]
ladder.rate_batch(games)

# Export all ratings
print(ladder.to_dict())
# {"alice": (mu, sigma), "bob": (mu, sigma), ...}
```

### BatchProcessor — one-shot bulk processing

Best for offline batch jobs where all games are known upfront.

```python
from openskill.batch import BatchProcessor, Game
from openskill.models.weng_lin.plackett_luce import PlackettLuce

model = PlackettLuce()

games = [
    Game(teams=[["a"], ["b"]]),
    Game(teams=[["c"], ["d"]], scores=[1, 0]),
    Game(teams=[["a"], ["c"]], ranks=[2, 1]),
]

# Sequential (single-threaded, deterministic)
proc = BatchProcessor(model, games, initial_mus={"a": 30.0})
result = proc.process(mode="sequential")
print(result)  # {"a": (mu, sigma), "b": (mu, sigma), ...}

# Parallel (multi-threaded waves)
result = proc.process(mode="parallel")

# Pipelined (overlap compute with scheduling)
result = proc.process(mode="pipelined")
```

### Works with all five models

```python
from openskill.models.weng_lin.plackett_luce import PlackettLuce
from openskill.models.weng_lin.bradley_terry_full import BradleyTerryFull
from openskill.models.weng_lin.bradley_terry_part import BradleyTerryPart
from openskill.models.weng_lin.thurstone_mosteller_full import ThurstoneMostellerFull
from openskill.models.weng_lin.thurstone_mosteller_part import ThurstoneMostellerPart

for ModelClass in [PlackettLuce, BradleyTerryFull, BradleyTerryPart,
                   ThurstoneMostellerFull, ThurstoneMostellerPart]:
    ladder = Ladder(ModelClass())
    ladder.rate(teams=[["alice"], ["bob"]])
    print(f"{ModelClass.__name__}: {ladder['alice'].mu:.2f}")
```

## Performance

Benchmarked on CPython 3.11.14 with 3 000 players.  Both datasets measured in
the same process run to ensure consistent comparison.

### Swiss — 13 500 1v1 games, 9 rounds

Uniform matchmaking: every player plays every round, games are independent
within a round.  9 large waves of 1 500 games each.

| Approach | PlackettLuce | BradleyTerryFull | BradleyTerryPart | TM Full | TM Part |
|----------|-------------:|-----------------:|-----------------:|--------:|--------:|
| `model.rate()` loop | 840 ms | 840 ms | 802 ms | 899 ms | 947 ms |
| `Ladder` (pure Python) | 174 ms | 157 ms | 127 ms | 169 ms | 192 ms |
| `Ladder` + Cython | 153 ms | 111 ms | 105 ms | 160 ms | 175 ms |
| **Speedup** | **5.5x** | **7.6x** | **7.6x** | **5.6x** | **5.4x** |

### Power-law — 5 000 mixed-team games, heavy repeat players

Simulates games where a small number of players are far more active than
others (power-law distribution).  Games use mixed team sizes (2v2, 3v3, etc.)
so per-game compute is heavier.  Creates deep dependency chains — 1 167 waves
averaging just 4.3 games each.  This is the worst case for wave parallelism
but still benefits from the per-game fast path.

| Approach | PlackettLuce | BradleyTerryFull | BradleyTerryPart | TM Full | TM Part |
|----------|-------------:|-----------------:|-----------------:|--------:|--------:|
| `model.rate()` loop | 837 ms | 807 ms | 796 ms | 852 ms | 872 ms |
| `Ladder` (pure Python) | 140 ms | 164 ms | 129 ms | 171 ms | 176 ms |
| `Ladder` + Cython | 120 ms | 140 ms | 110 ms | 184 ms | 165 ms |
| **Speedup** | **7.0x** | **5.8x** | **7.2x** | **5.0x** | **5.3x** |

All approaches produce **bit-identical** results across both datasets
(within 1e-9).  Speedups are in the same 5-7x range regardless of game
structure.

### Where the time goes

```
model.rate()    804 ms  ← deepcopy (27%) + UUID (23%) + validate + compute
Ladder.rate()   165 ms  ← just compute, no overhead
Ladder+Cy       142 ms  ← typed array access around compute
```

The `_compute()` math is the same in all cases — the speedup comes entirely
from removing wrapper overhead.

## Architecture notes

- **`_FastRating`**: Defined in `openskill/batch.py`.  A `__slots__` class
  with `.mu`, `.sigma`, and `.ordinal()`.  Drop-in substitute for the model's
  Rating class as far as `_compute()` is concerned.  No UUID, no `__dict__`.
- **Backing arrays**: `Ladder` stores all ratings in two contiguous
  `array.array('d')` buffers (mu and sigma).  `RatingView` objects are
  flyweight pointers into these arrays — 24 bytes each.
- **Wave scheduling**: `partition_waves()` groups independent games into
  waves that can be processed in parallel, while respecting data dependencies
  between games that share players.
- **No monkey-patching**: The existing `model.rate()` / `model._compute()`
  APIs are unchanged.  `Ladder` simply calls `_compute()` directly, skipping
  the `rate()` wrapper.
