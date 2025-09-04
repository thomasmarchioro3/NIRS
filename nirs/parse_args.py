"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.
"""

import argparse


def get_args():

    parser = argparse.ArgumentParser(
        prog="run_nirs", description="NIRS experiments with real NIDS.", epilog=""
    )

    parser.add_argument(
        "--nids",
        type=str,
        default="rf",
        help="NIDS to be used for the experiment. Options: rf.",
    )

    parser.add_argument(
        "--dataset",
        type=str,
        default="nb15",
        help="dataset to be used for the experiment. Options: nb15.",
    )
    parser.add_argument(
        "--nirs",
        type=str,
        default="heuristic",
        help="NIRS to be used for the experiment. Options: base, heuristic, ollama.",
    )
    parser.add_argument("--fpr", type=float, default=0.1, help="False positive rate.")

    parser.add_argument(
        "--eps",
        type=float,
        default=0.01,
        help="Max fraction of blocked flows in benign_window. Used only for HeuristicNIRS. Default: 0.1.",
    )

    parser.add_argument(
        "--k_prompt",
        type=int,
        default=10,
        help="Max number of examples from alert and benign window (2*k_prompt examples in total). Used only for OllamaNIRS. Default: 10.",
    )
    parser.add_argument(
        "--update_time_ms",
        type=int,
        default=1_800_000,
        help="Update time in milliseconds. Default: 1_800_000 (30 minutes).",
    )

    parser.add_argument(
        "--seed", type=int, default=42, help="Seed used for PRNG. Default: 42."
    )

    args = parser.parse_args()

    return args


def get_nids_pred_filename(nids_name: str, dataset_name: str, seed: int = 42):
    return f"{nids_name}_{dataset_name}_seed{seed}_pred.csv"


def get_resfile_name(
    nids_name: str,
    dataset_name: str,
    nirs_name: str,
    fpr: float,
    eps: float = 0.1,
    k_prompt: int = 10,
    seed: int = 42,
    update_time_ms: int = 1_800_000,
):

    fpr_pretty = str(fpr).replace(".", "_")

    resfile = f"{nids_name}_nids_{dataset_name}_{nirs_name}nirs_fpr{fpr_pretty}_update_{update_time_ms}_seed{seed}.csv"
    if nirs_name == "rule":
        eps_pretty = str(eps).replace(".", "_")
        resfile = f"{nids_name}_nids_{dataset_name}_{nirs_name}nirs_fpr{fpr_pretty}_eps{eps_pretty}_update_{update_time_ms}_seed{seed}.csv"
    elif nirs_name == "ollama":
        resfile = f"{nids_name}_nids_{dataset_name}_{nirs_name}nirs_fpr{fpr_pretty}_k{k_prompt}_update_{update_time_ms}_seed{seed}.csv"

    return resfile
