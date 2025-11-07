"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.

Example usage:

```sh
python -m experiments.run_nirs --help
```
"""
import os
import sys
import time

import numpy as np
import polars as pl

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from nirs.eval import eval_nirs
from nirs.datasets import load_dataset
from nirs import WindowNIRS, HeuristicNIRS, OllamaNIRS
from nids.utils import apply_quantile_threshold

from nirs.parse_args import get_args, get_resfile_name


def eval_nirs_real(
    df: pl.DataFrame,
    nirs: WindowNIRS,
    nids_pred: pl.Series,
    fpr: float,
    update_time_ms: float,
    seed: int,
) -> pl.DataFrame:
    # build a single dataframe for everything
    df = df.with_columns(
        pl.Series(values=np.arange(len(df)), name="idx"),
        pl.Series(values=np.zeros(len(df)), name="is_blocked"),
        pl.Series(values=nids_pred, name="nids_pred"),
    )

    df, threshold = apply_quantile_threshold(df, 1 - fpr)
    print(rf"Threshold at {fpr * 100}% FPR", threshold)

    df = df.drop("nids_pred")

    real_fpr = df.filter(pl.col("label") == 0)["is_alert"].mean()
    tpr = df.filter(pl.col("label") == 1)["is_alert"].mean()

    print(f"FPR: {real_fpr}")
    print(f"TPR: {tpr}")

    res_df = eval_nirs(df, nirs, update_time_ms, seed)

    return res_df


def eval_nirs_ideal(
    df: pl.DataFrame,
    nirs: WindowNIRS,
    update_time_ms: float,
    seed: int,
) -> pl.DataFrame:
    # build a single dataframe for everything
    df = df.with_columns(
        pl.Series(values=np.arange(len(df)), name="idx"),
        pl.Series(values=np.zeros(len(df)), name="is_blocked"),
        pl.col("label").alias("is_alert"),
    )

    res_df = eval_nirs(df, nirs, update_time_ms, seed)

    return res_df


if __name__ == "__main__":
    args = get_args()

    seed = args.seed
    fpr = args.fpr

    fpr_pretty = str(fpr).replace(".", "_")

    max_alert_window_idle_ms = 60_000
    max_alert_window_len_ms = 600_000
    benign_traffic_window_len_ms = 600_000
    max_rules = 10
    update_time_ms = args.update_time_ms

    dataset_name = args.dataset
    nirs_name = args.nirs

    print("-" * 20)
    print(f"Dataset: {dataset_name}")
    print(f"NIDS: {args.nids}")
    print(f"NIRS: {nirs_name}")
    print(f"FPR: {fpr}")
    print(f"Update time: {update_time_ms}")
    print(f"Seed: {seed}")

    match args.nirs:
        case "base":
            # NOTE: BaseNIRS does nothing and should only be used for debugging
            NIRS_Factory = lambda: WindowNIRS(
                max_alert_window_idle_ms=max_alert_window_idle_ms,
                max_alert_window_len_ms=max_alert_window_len_ms,
                benign_traffic_window_len_ms=benign_traffic_window_len_ms,
                max_rules=max_rules,
            )
        case "heuristic":
            print(f"Epsilon: {args.eps}")
            NIRS_Factory = lambda: HeuristicNIRS(
                max_alert_window_idle_ms=max_alert_window_idle_ms,
                max_alert_window_len_ms=max_alert_window_len_ms,
                benign_traffic_window_len_ms=benign_traffic_window_len_ms,
                max_rules=max_rules,
                frac_benign_tolerance=args.eps,
            )

        case "ollama":
            print(f"Number of flow examples in the LLM prompt: {args.k_prompt}")
            NIRS_Factory = lambda: OllamaNIRS(
                max_alert_window_idle_ms=max_alert_window_idle_ms,
                max_alert_window_len_ms=max_alert_window_len_ms,
                benign_traffic_window_len_ms=benign_traffic_window_len_ms,
                max_rules=max_rules,
                num_examples_prompt=args.k_prompt,
            )

        case _:
            raise NotImplementedError

    tic = time.perf_counter()
   
    df = load_dataset(dataset_name)
    print(df.head())

    if args.nids == "ideal":
        nirs = NIRS_Factory()
        res_df = eval_nirs_ideal(df, nirs, update_time_ms, seed)
    else:
        nids_pred = pl.read_csv(
            f"results/temp/nids/{args.nids}_{args.dataset}_seed{args.seed}_pred.csv"
        )["pred"]
        nirs = NIRS_Factory()
        res_df = eval_nirs_real(df, nirs, nids_pred, fpr, update_time_ms, seed)

    toc = time.perf_counter()
    print(f"Time: {toc - tic}")

    outdir = "results/temp"
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    outfile = get_resfile_name(
        args.nids, 
        dataset_name, 
        nirs_name, 
        fpr, 
        args.eps, 
        args.k_prompt, 
        seed, 
        update_time_ms
    )

    outfile = os.path.join(outdir, outfile)

    res_df.write_csv(outfile)
    print(f"Results saved to {outfile}")

    res_df = res_df.with_columns(
        df["label"],
        pl.col("is_blocked"),
    )

    cbr = res_df.filter(pl.col("label") == 1)["is_blocked"].mean()
    wbr = res_df.filter(pl.col("label") == 0)["is_blocked"].mean()

    print(f"CBR: {cbr}")
    print(f"WBR: {wbr}")
