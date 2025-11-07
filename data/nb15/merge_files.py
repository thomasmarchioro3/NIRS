import os

COLUMN_NAMES = [
    "srcip",
    "sport",
    "dstip",
    "dsport",
    "proto",
    "state",
    "dur",
    "sbytes",
    "dbytes",
    "sttl",
    "dttl",
    "sloss",
    "dloss",
    "service",
    "Sload",
    "Dload",
    "Spkts",
    "Dpkts",
    "swin",
    "dwin",
    "stcpb",
    "dtcpb",
    "smeansz",
    "dmeansz",
    "trans_depth",
    "res_bdy_len",
    "Sjit",
    "Djit",
    "Stime",
    "Ltime",
    "Sintpkt",
    "Dintpkt",
    "tcprtt",
    "synack",
    "ackdat",
    "is_sm_ips_ports",
    "ct_state_ttl",
    "ct_flw_http_mthd",
    "is_ftp_login",
    "ct_ftp_cmd",
    "ct_srv_src",
    "ct_srv_dst",
    "ct_dst_ltm",
    "ct_src_ ltm",
    "ct_src_dport_ltm",
    "ct_dst_sport_ltm",
    "ct_dst_src_ltm",
    "attack_cat",
    "Label",
]

if __name__ == "__main__":

    root_dir = "data/nb15"

    csv_files = [os.path.join(root_dir, f"UNSW-NB15_{i}.csv") for i in range(1, 5)]
    outfile = os.path.join(root_dir, "nb15.csv")

    header = ",".join(COLUMN_NAMES) + "\n"

    with open(outfile, "w") as f:
        f.write(header)

        for csv_file in csv_files:
            with open(csv_file, "r") as fin:
                f.write(fin.read())

