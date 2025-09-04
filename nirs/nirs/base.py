"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.
"""

from typing import Callable

import numpy as np
import polars as pl

from nirs.iptables import IptablesRule

class BaseNIRS:

    def __init__(self) -> None:

        self.ruleset: list[IptablesRule] = []
        pass

    def apply_rules(self, X: pl.DataFrame) -> np.ndarray:
        
        idx_blocked = np.asarray([])
        return idx_blocked

    def update(self, df: pl.DataFrame) -> None:

        return


def update_ruleset_default(ruleset: list, alert_df: pl.DataFrame, benign_df: pl.DataFrame, max_rules: int):
        if len(ruleset) > max_rules:
            return ruleset[-max_rules:]
        return ruleset


class WindowNIRS(BaseNIRS):
    

    def __init__(
        self, 
        max_alert_window_idle_ms: int, 
        max_alert_window_len_ms: int, 
        benign_traffic_window_len_ms: int, 
        max_rules: int,
        update_ruleset_fn: Callable | None = None
        ):

        super().__init__()

        self.max_alert_window_idle_ms = max_alert_window_idle_ms
        self.max_alert_window_len_ms = max_alert_window_len_ms
        self.benign_traffic_window_len_ms = benign_traffic_window_len_ms
        self.max_rules = max_rules


        self.benign_window = pl.DataFrame(schema={
            'timestamp': pl.Int64,
            'src_ip': pl.Utf8,
            'src_port': pl.Int64,
            'dst_ip': pl.Utf8,
            'dst_port': pl.Int64,
            'src_data': pl.Int64,
            'dst_data': pl.Int64,
            'protocol': pl.Utf8,
        })
        self.alert_window = pl.DataFrame(schema={
            'timestamp': pl.Int64,
            'src_ip': pl.Utf8,
            'src_port': pl.Int64,
            'dst_ip': pl.Utf8,
            'dst_port': pl.Int64,
            'src_data': pl.Int64,
            'dst_data': pl.Int64,
            'protocol': pl.Utf8,
        })

        self.ruleset: list[IptablesRule] = []

        if update_ruleset_fn is None:
            self.update_ruleset = update_ruleset_default
        else:
            self.update_ruleset = update_ruleset_fn


    def apply_rules(self, X: pl.DataFrame):
        
        idx_blocked = np.asarray([])
        for rule in self.ruleset:
            idx_blocked = np.append(idx_blocked, rule.match_df(X))

        return idx_blocked


    def update(self, df: pl.DataFrame):

        benign_df = df.filter(pl.col("is_alert") == 0)
        alert_df = df.filter(pl.col("is_alert") == 1)

        self.ingest_benign_df(benign_df)

        if len(alert_df) > 0:
            self.ingest_alert_df(alert_df)
            self.ruleset = self.update_ruleset(self.ruleset, self.alert_window, self.benign_window, self.max_rules)

        return


    def ingest_benign_df(self, benign_df: pl.DataFrame):
        self.benign_window  = pl.concat([self.benign_window, benign_df[self.benign_window.columns]], how="vertical")

        if self.benign_window.shape[0] > 0:
            t_max = self.alert_window["timestamp"].max()

            if not isinstance(t_max, (int, float)):
                t_max = float("inf")

            self.max_timestamp = t_max
            self.benign_window = self.benign_window.filter(
                pl.col("timestamp") > self.max_timestamp - self.benign_traffic_window_len_ms
            )


        return

    def ingest_alert_df(self, alert_df: pl.DataFrame):
        
        if self.alert_window.shape[0] == 0:
            self.alert_window = alert_df[self.alert_window.columns]
            return
        
        t_min = alert_df["timestamp"].min()
        t_max = self.alert_window["timestamp"].max()

        if not isinstance(t_min, (int, float)):
            t_min = 0

        if not isinstance(t_max, (int, float)):
            t_max = float("inf")

        if t_max - t_min > self.max_alert_window_idle_ms:
            self.alert_window = alert_df[self.alert_window.columns]
        else:
            self.alert_window  = pl.concat([self.alert_window, alert_df[self.alert_window.columns]], how="vertical")

        self.max_timestamp = t_max
        self.alert_window = self.alert_window.filter(pl.col("timestamp") > self.max_timestamp - self.max_alert_window_len_ms)

        return

