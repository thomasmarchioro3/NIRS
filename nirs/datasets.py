"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.
"""


from typing import Literal
import polars as pl

from .network import is_inter_subnet

PRETTY_DATASET_NAME = {
    "nb15": "NB15",
}


def get_pretty_dataset_name(name: str):
    """
    Args:
        name (str): The name of the dataset.

    Returns:
        str: The prettier name if it exists, otherwise the original name.
    """
    return PRETTY_DATASET_NAME.get(name, name)


def load_dataset(name: Literal["nb15"], percent10: bool = False):
    """
    Args:
        name (str): The name of the dataset to load. Currently supports "nb15".
        percent10 (bool, optional): Whether to load the 10% sample of the dataset. Defaults to False.
    """

    if name == "nb15":
        return load_nb15(percent10)
    else:
        raise NotImplementedError


def load_nb15(percent10: bool = False):

    if percent10:
        filename = "data/nb15/nb15_random10.csv"
    else:
        filename = "data/nb15/nb15.csv"

    df = pl.read_csv(filename, ignore_errors=True)

    df = df.rename(
        {
            "srcip": "src_ip",
            "dstip": "dst_ip",
            "sport": "src_port",
            "dsport": "dst_port",
            "proto": "protocol",
            "sbytes": "src_data",
            "dbytes": "dst_data",
            "Stime": "timestamp",
            "Label": "label",
            "attack_cat": "type",
        }
    )

    # sort by timestamp
    df = df.sort("timestamp")

    label_fixes = {
        "Backdoors": "Backdoor",
    }

    df = df.with_columns(
        pl.col("type")
        .fill_null("Normal")
        .map_elements(lambda x: label_fixes.get(x, x), return_dtype=pl.String)
        .str.strip_chars(" ")
        .alias("type"),
        pl.col("timestamp") * 1_000,
        pl.struct("src_ip", "dst_ip")
        .map_elements(
            lambda x: is_inter_subnet(x["src_ip"], x["dst_ip"]), return_dtype=pl.Boolean
        )
        .alias("inter_subnet"),
    )

    df = df[
        [
            "src_ip",
            "dst_ip",
            "src_port",
            "dst_port",
            "protocol",
            "timestamp",
            "src_data",
            "dst_data",
            "inter_subnet",
            "label",
            "type",
        ]
    ]

    return df


if __name__ == "__main__":

    import warnings

    warnings.filterwarnings("ignore", category=pl.exceptions.ChronoFormatWarning)

    df = load_nb15(percent10=False)
