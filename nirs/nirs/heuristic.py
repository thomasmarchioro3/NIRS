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

from .base import WindowNIRS

from nirs.iptables import IptablesRule


def _update_ruleset(
    ruleset: list,
    alert_df: pl.DataFrame,
    benign_df: pl.DataFrame,
    max_rules: int,
    frac_benign_tolerance: float = 1e-1,
):
    # apply current ruleset first (avoids repeating rules)
    alert_df = alert_df.with_columns(
        pl.Series(values=np.arange(len(alert_df)), name="idx")
    )
    benign_df = benign_df.with_columns(
        pl.Series(values=np.arange(len(benign_df)), name="idx")
    )
    for rule in ruleset:
        idx_blocked_alert = rule.match_df(alert_df)
        alert_df = alert_df.filter(~pl.col("idx").is_in(idx_blocked_alert))
        idx_blocked_benign = rule.match_df(benign_df)
        benign_df = benign_df.filter(~pl.col("idx").is_in(idx_blocked_benign))

    # Get list of all IPs sorted by counts for both benign_df and alert_df
    alert_ip_counts = (
        pl.concat([alert_df["src_ip"].alias("ip"), alert_df["dst_ip"].alias("ip")])
        .to_pandas()
        .value_counts()
        .to_dict()
    )
    benign_ip_counts = (
        pl.concat([benign_df["src_ip"].alias("ip"), benign_df["dst_ip"].alias("ip")])
        .to_pandas()
        .value_counts()
        .to_dict()
    )

    for ip in alert_ip_counts.keys():
        if ip in benign_ip_counts.keys():
            if benign_ip_counts[ip] > frac_benign_tolerance * len(benign_df):
                continue

        rule_str = f"-A FORWARD -s {ip} -j DROP"
        rule = IptablesRule(rule_str)
        if str(rule) in [str(r) for r in ruleset]:
            return ruleset
        ruleset.append(rule)
        break

    if len(ruleset) > max_rules:
        return ruleset[-max_rules:]
    return ruleset


class HeuristicNIRS(WindowNIRS):
    def __init__(
        self,
        max_alert_window_idle_ms: int,
        max_alert_window_len_ms: int,
        benign_traffic_window_len_ms: int,
        max_rules: int,
        frac_benign_tolerance: float = 1e-1,
    ):
        super().__init__(
            max_alert_window_idle_ms,
            max_alert_window_len_ms,
            benign_traffic_window_len_ms,
            max_rules,
            update_ruleset_fn=lambda max_alert_window_idle_ms, max_alert_window_len_ms, benign_traffic_window_len_ms, max_rules: _update_ruleset(
                max_alert_window_idle_ms,
                max_alert_window_len_ms,
                benign_traffic_window_len_ms,
                max_rules,
                frac_benign_tolerance=frac_benign_tolerance,
            ),
        )
