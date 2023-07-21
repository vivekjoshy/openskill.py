"""
All objects specific to each model.
"""

from typing import List

from openskill.models.weng_lin import (
    BradleyTerryFull,
    BradleyTerryFullRating,
    BradleyTerryPart,
    BradleyTerryPartRating,
    PlackettLuce,
    PlackettLuceRating,
    ThurstoneMostellerFull,
    ThurstoneMostellerFullRating,
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
    "MODELS",
]

MODELS = [
    PlackettLuce,
    BradleyTerryFull,
    BradleyTerryPart,
    ThurstoneMostellerFull,
    ThurstoneMostellerPart,
]
