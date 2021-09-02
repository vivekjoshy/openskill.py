from typing import List, Optional, Union

from openskill.constants import mu as default_mu
from openskill.constants import sigma as default_sigma


class Rating:
    def __init__(
        self, mu: Optional[float] = None, sigma: Optional[float] = None, **options
    ):
        # Calculate Mu and Sigma
        self.mu = mu if mu else default_mu(**options)
        self.sigma = sigma if sigma else default_sigma(**options)

    def __repr__(self):
        return f"Rating(mu={self.mu}, sigma={self.sigma})"

    def __eq__(self, other):
        if len(other) == 2:
            if self.mu == other[0] and self.sigma == other[1]:
                return True
            else:
                return False


def create_rating(rating_list: List[Union[int, float]]):
    return Rating(mu=rating_list[0], sigma=rating_list[1])
