"""
All models described in :cite:p:`JMLR:v12:weng11a` are implemented in this
module. Some convenience and original methods are also provided to make it
easier to instantiate and use the models.
"""

from typing import List

from openskill.models.weng_lin.bradley_terry_full import (
    BradleyTerryFull,
    BradleyTerryFullRating,
)
from openskill.models.weng_lin.bradley_terry_part import (
    BradleyTerryPart,
    BradleyTerryPartRating,
)
from openskill.models.weng_lin.plackett_luce import PlackettLuce, PlackettLuceRating
from openskill.models.weng_lin.thurstone_mosteller_full import (
    ThurstoneMostellerFull,
    ThurstoneMostellerFullRating,
)
from openskill.models.weng_lin.thurstone_mosteller_part import (
    ThurstoneMostellerPart,
    ThurstoneMostellerPartRating,
)

__all__: List[str] = [
    "BradleyTerryFull",
    "BradleyTerryFullRating",
    "BradleyTerryPart",
    "BradleyTerryPartRating",
    "PlackettLuce",
    "PlackettLuceRating",
    "ThurstoneMostellerFull",
    "ThurstoneMostellerFullRating",
    "ThurstoneMostellerPart",
    "ThurstoneMostellerPartRating",
]
