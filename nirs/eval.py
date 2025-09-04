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

from nirs import BaseNIRS

def seed_all(seed: int):
    np.random.seed(seed)


def eval_nirs(
    df: pl.DataFrame,
    nirs: BaseNIRS,
    update_time_ms: float = 30_000,
    seed: int | None = None,
) -> pl.DataFrame:
    """
    Evaluates a network intrusion detection system (NIRS) on a DataFrame of network traffic data containing basic flow information.

    Args:
        df (DataFrame): DataFrame with columns: timestamp, src_ip, dst_ip, protocol, src_port, dst_port, is_alert.
        nirs (BaseNIRS): An extension of BaseNIRS to be evaluated.
        update_time_ms (float): Time interval in milliseconds between NIRS updates.
        seed (int | None): Seed for random number generator
    """

    if seed is not None:
        seed_all(seed)

    # initialize columns
    df = df.with_columns(pl.Series(values=np.arange(len(df)), name="idx"))
    df = df.with_columns(pl.Series(values=np.zeros(len(df)), name="is_blocked"))

    # iteration counter
    it = 0

    t_current = df["timestamp"].min()
    t_min = t_current

    while (
        len(df.filter(pl.col("timestamp") > t_current).filter(pl.col("is_alert") == 1))
        > 0
    ):
        """
        Evaluation loop:
        - apply rules at time t_current to all df
        - get to t_next (t_current + update_time_ms)
        - update blocked (only between t_current t_next)
        - update rules
        - move t_current to t_next
        """

        print("Current time:", (t_current - t_min) / 1000, "seconds")

        # if no connections in current window, move to next window
        if (
            len(
                df.filter(pl.col("timestamp") >= t_current).filter(
                    pl.col("timestamp") <= t_current + update_time_ms
                )
            )
            == 0
        ):
            t_current += update_time_ms
            it += 1
            continue

        # apply current rules
        idx_blocked = nirs.apply_rules(df)

        # ensure minimum update time
        t_next = t_current + update_time_ms

        # update blocked (only between t_current t_next)
        df = df.with_columns(
            pl.when(
                pl.col("idx").is_in(idx_blocked)
                & (pl.col("timestamp") <= t_next)
                & (pl.col("timestamp") >= t_current)
                & pl.col("inter_subnet")
            )
            .then(1)
            .otherwise(pl.col("is_blocked"))
            .alias("is_blocked")
        )

        df_alert_not_blocked = df.filter(
            (pl.col("is_alert") == 1)
            & (pl.col("timestamp") <= t_next)
            & (pl.col("timestamp") >= t_current)
            & pl.col("inter_subnet")
            & (pl.col("is_blocked") == 0)
            & ((pl.col("src_data") > 0) | (pl.col("dst_data") > 0))
        )

        if len(df_alert_not_blocked) == 0:
            t_current += update_time_ms
            it += 1
            continue

        print(df_alert_not_blocked["src_ip", "dst_ip", "src_data", "dst_data"])

        # update rules
        nirs.update(
            df.filter(
                ~(pl.col("idx").is_in(idx_blocked))
                & (pl.col("timestamp") <= t_next)
                & (pl.col("timestamp") >= t_current)
                & pl.col("inter_subnet")
                & ((pl.col("src_data") > 0) | (pl.col("dst_data") > 0))
            )
        )

        t_current = t_next

        it += 1

    res_df = df[["timestamp", "is_blocked"]]

    for rule in nirs.ruleset:
        print(str(rule))

    return res_df
