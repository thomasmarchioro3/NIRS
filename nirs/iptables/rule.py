"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.
"""

import numpy as np
import polars as pl

from .parser import parse_iptables_rule
from .match import match_rule_df


class IptablesRule:
    """
    A class to represent an iptables rule, storing both its string and dictionary representation.
    """

    def __init__(self, rule_str: str):
        self.rule = {}

        print(rule_str)

        self.rule["str"] = f"{rule_str}"
        self.rule["dict"] = parse_iptables_rule(rule_str)

    def match_df(self, X: pl.DataFrame) -> np.ndarray:
        return match_rule_df(X, self.rule["dict"])

    def get_rule_dict(self):
        return self.rule["dict"]

    def __str__(self):
        return self.rule["str"]

    def __repr__(self):
        return self.rule["str"]