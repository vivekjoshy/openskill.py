Bulk Rating
===========

``Ladder`` and ``BatchProcessor`` provide a high-performance path for processing
many games without the per-call overhead of ``model.rate()``.  No extra
dependencies are required -- the speedup comes from architectural changes, not
native code.


Why It's Faster
---------------

``model.rate()`` does three expensive things on **every** call:

.. list-table::
   :header-rows: 1

   * - Overhead
     - Cost (13 500 games)
     - Needed?
   * - ``copy.deepcopy()``
     - ~240 ms
     - No -- Ladder owns the arrays
   * - ``uuid.uuid4()`` per Rating
     - ~170 ms (kernel syscall)
     - No -- ``_compute()`` never reads ``.id``
   * - Input validation
     - ~50 ms
     - No -- Ladder controls inputs

``Ladder`` and ``BatchProcessor`` skip all three.  Rating objects are replaced
with ``_FastRating`` -- a minimal ``__slots__`` class with just ``.mu``,
``.sigma``, and ``.ordinal()``.  No UUID, no ``__dict__``, no deepcopy.


Ladder -- Stateful Rating Tracker
---------------------------------

Best for online/streaming scenarios where games arrive over time.

.. code-block:: python

   from openskill.models import PlackettLuce
   from openskill.ladder import Ladder

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
   from openskill.batch import Game

   games = [
       Game(teams=[["alice"], ["charlie"]]),
       Game(teams=[["bob"], ["dave"]]),      # independent -- runs in same wave
       Game(teams=[["alice"], ["bob"]]),      # depends on above -- next wave
   ]
   ladder.rate_batch(games)

   # Export all ratings
   print(ladder.to_dict())
   # {"alice": (mu, sigma), "bob": (mu, sigma), ...}


BatchProcessor -- One-Shot Bulk Processing
-------------------------------------------

Best for offline batch jobs where all games are known upfront.

.. code-block:: python

   from openskill.batch import BatchProcessor, Game
   from openskill.models import PlackettLuce

   model = PlackettLuce()

   games = [
       Game(teams=[["a"], ["b"]]),
       Game(teams=[["c"], ["d"]], scores=[1, 0]),
       Game(teams=[["a"], ["c"]], ranks=[2, 1]),
   ]

   # Sequential (single-threaded, deterministic)
   proc = BatchProcessor(model, n_workers=1)
   result = proc.process(games)
   print(result)  # {"a": (mu, sigma), "b": (mu, sigma), ...}

   # Parallel (multi-worker pipeline)
   proc = BatchProcessor(model, n_workers=4)
   result = proc.process(games)

.. note::

   Multi-worker batch processing requires free-threaded Python
   (version 3.13t, 3.14t, or later) to benefit from true parallelism.
   On standard Python builds with the GIL enabled, multiple workers use
   separate processes with serialization overhead.  If you are not on a
   free-threaded build, use ``n_workers=1`` or use ``Ladder`` directly.


All Five Models
^^^^^^^^^^^^^^^

Both ``Ladder`` and ``BatchProcessor`` work with all five Weng-Lin models:

.. code-block:: python

   from openskill.models import (
       PlackettLuce, BradleyTerryFull, BradleyTerryPart,
       ThurstoneMostellerFull, ThurstoneMostellerPart,
   )
   from openskill.ladder import Ladder

   for ModelClass in [PlackettLuce, BradleyTerryFull, BradleyTerryPart,
                      ThurstoneMostellerFull, ThurstoneMostellerPart]:
       ladder = Ladder(ModelClass())
       ladder.rate(teams=[["alice"], ["bob"]])
       print(f"{ModelClass.__name__}: {ladder['alice'].mu:.2f}")


Optional Cython Extension
--------------------------

An optional Cython extension provides an additional ~10-15% speedup on top
of the pure-Python fast path.  The extension is compiled automatically at
install time when Cython is present:

.. code-block:: shell

   # Install with Cython support (auto-builds the extension):
   uv pip install "openskill[cython]"

   # Or with plain pip:
   pip install "openskill[cython]"

For development, you can rebuild the extension in-place without reinstalling:

.. code-block:: shell

   python setup.py build_ext --inplace

Cython is detected automatically at runtime.  If the compiled extension is
present, ``Ladder`` uses it; otherwise it falls back to the pure-Python path
transparently.  You can check which path is active:

.. code-block:: python

   from openskill.ladder import _HAS_CYTHON
   print(_HAS_CYTHON)  # True if Cython extension loaded


Performance
-----------

Benchmarked on CPython 3.11.14 with 3 000 players.

Swiss -- 13 500 1v1 Games
^^^^^^^^^^^^^^^^^^^^^^^^^^

Uniform matchmaking: every player plays every round, games are independent
within a round.  9 large waves of 1 500 games each.

.. list-table::
   :header-rows: 1

   * - Approach
     - PlackettLuce
     - BradleyTerryFull
     - BradleyTerryPart
     - TM Full
     - TM Part
   * - ``model.rate()`` loop
     - 840 ms
     - 840 ms
     - 802 ms
     - 899 ms
     - 947 ms
   * - ``Ladder`` (pure Python)
     - 174 ms
     - 157 ms
     - 127 ms
     - 169 ms
     - 192 ms
   * - ``Ladder`` + Cython
     - 153 ms
     - 111 ms
     - 105 ms
     - 160 ms
     - 175 ms
   * - **Speedup**
     - **5.5x**
     - **7.6x**
     - **7.6x**
     - **5.6x**
     - **5.4x**


Power-Law -- 5 000 Mixed-Team Games
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Simulates games where a small number of players are far more active than
others (power-law distribution).  Games use mixed team sizes (2v2, 3v3, etc.)
so per-game compute is heavier.  Creates deep dependency chains -- 1 167 waves
averaging just 4.3 games each.

.. list-table::
   :header-rows: 1

   * - Approach
     - PlackettLuce
     - BradleyTerryFull
     - BradleyTerryPart
     - TM Full
     - TM Part
   * - ``model.rate()`` loop
     - 837 ms
     - 807 ms
     - 796 ms
     - 852 ms
     - 872 ms
   * - ``Ladder`` (pure Python)
     - 140 ms
     - 164 ms
     - 129 ms
     - 171 ms
     - 176 ms
   * - ``Ladder`` + Cython
     - 120 ms
     - 140 ms
     - 110 ms
     - 184 ms
     - 165 ms
   * - **Speedup**
     - **7.0x**
     - **5.8x**
     - **7.2x**
     - **5.0x**
     - **5.3x**

All approaches produce **bit-identical** results across both datasets
(within 1e-9).  Speedups are in the same 5--7x range regardless of game
structure.


Architecture Notes
------------------

- **_FastRating**: Defined in ``openskill.batch``.  A ``__slots__`` class
  with ``.mu``, ``.sigma``, and ``.ordinal()``.  Drop-in substitute for the
  model's Rating class as far as ``_compute()`` is concerned.  No UUID, no
  ``__dict__``.
- **Backing arrays**: ``Ladder`` stores all ratings in two contiguous
  ``array.array('d')`` buffers (mu and sigma).  ``RatingView`` objects are
  flyweight pointers into these arrays -- 24 bytes each.
- **Wave scheduling**: ``partition_waves()`` groups independent games into
  waves that can be processed in parallel, while respecting data dependencies
  between games that share players.
- **No monkey-patching**: The existing ``model.rate()`` / ``model._compute()``
  APIs are unchanged.  ``Ladder`` simply calls ``_compute()`` directly,
  skipping the ``rate()`` wrapper.
