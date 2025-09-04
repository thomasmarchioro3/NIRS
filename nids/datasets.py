"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.
"""

import numpy as np
import pandas as pd


dataset_name_dict = {
    "nb15": "NB15",
}

def load_dataset(name: str, percent10: bool=True) -> [np.ndarray, np.ndarray, np.ndarray]:
    if name == "nb15":
        return load_nb15(percent10)
    else:
        raise NotImplementedError


def load_nb15(percent10=True):
    
    if percent10:
        filename = "data/nb15/nb15_random10.csv"
    else:
        filename = "data/nb15/nb15.csv"

    train_size = 0.3

    df: pd.DataFrame = pd.read_csv(filename)

    df = df.rename(columns={
        "srcip": "src_ip",
        "dstip": "dst_ip",
        "sport": "src_port",
        "dsport": "dst_port",
        "proto": "protocol", 
        "Stime": "timestamp",
        "Label": "label",
        "attack_cat": "type",
    })

    # sort by timestamp
    df.sort_values(by="timestamp", inplace=True)

    num_columns = [ 
        #'src_port', 
        'dst_port', 'dur', 'sbytes', 'dbytes', 'sttl', 'dttl', 'sloss',
        'dloss', 'Sload', 'Dload', 'Spkts', 'Dpkts', 'swin', 'dwin', 'stcpb',
        'dtcpb', 'smeansz', 'dmeansz', 'trans_depth', 'res_bdy_len', 'Sjit',
        'Djit', 'Sintpkt', 'Dintpkt', 'tcprtt', 'synack',
        'ackdat', 'is_sm_ips_ports', 'ct_state_ttl', 'ct_flw_http_mthd',
        'is_ftp_login', 'ct_ftp_cmd', 'ct_srv_src', 'ct_srv_dst', 'ct_dst_ltm',
        'ct_src_ ltm', 'ct_src_dport_ltm', 'ct_dst_sport_ltm', 'ct_dst_src_ltm',
    ]

    X = df[num_columns]
    y = df["label"].astype(int)
    

    for col in X.columns:
        X.loc[:, col] = pd.to_numeric(X[col], errors='coerce').astype(float)

    train_len = int(train_size * len(df))

    X_train = X.iloc[:train_len]
    y_train = y.iloc[:train_len]

    X_test = X.iloc[train_len:]
    y_test = y.iloc[train_len:]

    X_train = X_train.reset_index(drop=True)
    y_train = y_train.reset_index(drop=True)
    X_test = X_test.reset_index(drop=True)
    y_test = y_test.reset_index(drop=True)

    X_train = X_train.astype(float).to_numpy()
    X_test = X_test.astype(float).to_numpy()
    y_train = y_train.to_numpy()
    y_test = y_test.to_numpy()

    return X_train, X_test, y_train, y_test

