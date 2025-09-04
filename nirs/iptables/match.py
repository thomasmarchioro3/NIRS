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


def is_in_subnet(x: str, subnet: str):
    """
    Check if an IP address is in a given subnet.
    
    Args:
        x (str): IP address, e.g. "10.2.0.4"
        subnet (str): subnet, e.g. "10.2.0.0/16"

    Returns:
        bool: True if x is in subnet, False otherwise.
    """

    netmask = subnet.split("/")[1]
    if netmask == "32":
        return x == subnet.split("/")[0]
    elif netmask == "24":
        ip_net = ".".join(subnet.split(".")[:3])
        return x.startswith(ip_net)
    elif netmask == "16":
        ip_net = ".".join(subnet.split(".")[:2])
        return x.startswith(ip_net)
    elif netmask == "8":
        ip_net = ".".join(subnet.split(".")[:1])
        return x.startswith(ip_net)
    return False

def match_ip(col: str, ip: str):
    if "/" in ip[-4:]:
        return pl.col(col).map_elements(lambda x: is_in_subnet(x, ip), return_dtype=pl.Boolean)
    return pl.col(col) == ip

def match_port(col: str, port: str):
    return pl.col(col) == int(port)

def match_data(col: str):
    return pl.col(col) > 0

def match_rule_df(X: pl.DataFrame, rule: dict) -> np.ndarray:
    """
    Rule matching function for polars dataframe of network traffic data.

    Example of rule:
    {
        "option": "-A",
        "table": "INPUT",
        "protocol": "any",
        "src_ip": "10.2.0.0/24",
        "dst_ip": "any",
        "src_port": "any",
        "dst_port": "any",
        "jump": "DROP"
    }

    Args:
        X (DataFrame): DataFrame with columns: timestamp, src_ip, dst_ip, protocol, src_port, dst_port, is_alert.
        rule (dict): Dictionary with keys: protcol, src_ip, dst_ip, src_port, dst_port

    Returns:
        np.ndarray: Array of indices of blocked alerts
    """

    if rule["protocol"] != "any":
        X = X.filter(pl.col("protocol") == rule["protocol"])

    if rule["src_ip"] != "any":
        X = X.filter((match_ip("src_ip", rule["src_ip"]) & match_data("src_data")) | (match_ip("dst_ip", rule["src_ip"]) & match_data("dst_data")))

    if rule["dst_ip"] != "any" and rule["src_port"] == "any" and rule["dst_port"] == "any":
        # case -A INPUT -d <dst_ip>[/<subnet>] -p <protocol> -j DROP
        X = X.filter((match_ip("dst_ip", rule["dst_ip"]) & match_data("src_data")) | (match_ip("src_ip", rule["dst_ip"]) & match_data("dst_data")))

    elif rule["dst_ip"] != "any" and rule["src_port"] == "any" and rule["dst_port"] != "any":
        # case -A INPUT -d <dst_ip>[/<subnet>] -p <protocol> --dport <dst_port> -j DROP
        # the protocol being != any is verified by the parser
        X = X.filter(
            (
                match_ip("src_ip", rule["dst_ip"]) & match_port("src_port", rule["dst_port"]) & match_data("src_data")
            ) | (
                match_ip("dst_ip", rule["dst_ip"]) & match_port("dst_port", rule["dst_port"]) & match_data("dst_data")
            )
        )
        
    return X["idx"].to_numpy()
