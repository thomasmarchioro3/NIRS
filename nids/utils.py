"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.
"""

import polars as pl

def apply_quantile_threshold(df: pl.DataFrame, quantile: float) -> [pl.DataFrame, float]:

    threshold = df.filter(pl.col("nids_pred") >= 0).filter(pl.col("label") == 0)["nids_pred"].quantile(quantile)

    df = df.with_columns(
        pl.when(pl.col('nids_pred') > threshold)
        .then(1)
        .otherwise(0)
        .alias("is_alert")
    )

    return df, threshold
