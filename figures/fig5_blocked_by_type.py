import os

import numpy as np
import matplotlib.pyplot as plt
import polars as pl

from nirs.datasets import load_dataset, get_pretty_dataset_name
from nids.utils import apply_quantile_threshold
from nirs.parse_args import get_args, get_resfile_name, get_nidspredfile_name

if __name__ == "__main__":
    
    args = get_args()

    nids_dir = "results/temp/nids"
    nirs_dir = "results/temp/nirs"

    dataset_name = args.dataset
    nids_name = args.nids

    eps = args.eps
    k_prompt = args.k_prompt
    update_time_ms = args.update_time_ms
    fpr = args.fpr
    seed = args.seed

    fpr_pretty = str(fpr).replace(".", "_")
    eps_pretty = str(eps).replace(".", "_")


    resrulefile = get_resfile_name(
        args.nids, 
        dataset_name, 
        "rule", 
        fpr, 
        eps, 
        k_prompt, 
        seed, 
        update_time_ms
    )
    resaifile = get_resfile_name(
        args.nids, 
        dataset_name, 
        "ai", 
        fpr, 
        eps, 
        k_prompt, 
        seed, 
        update_time_ms
    )

    nids_filename = get_nidspredfile_name(args.nids, dataset_name, seed)

    resrule_filename = os.path.join(nirs_dir, resrulefile)
    resai_filename = os.path.join(nirs_dir, resaifile)
    nids_filename = os.path.join(nids_dir, nids_filename)

    assert os.path.isfile(resrule_filename)
    assert os.path.isfile(resai_filename)
    assert os.path.isfile(nids_filename)
    

    df = load_dataset(name=dataset_name)

    df = df["label", "type"]


    res_df = pl.read_csv(resrule_filename)
    df = df.with_columns(
        res_df["is_blocked"].alias("is_blocked_rule"),
    )

    res_df = pl.read_csv(resai_filename)
    df = df.with_columns(
        res_df["is_blocked"].alias("is_blocked_ai"),
    )

    nids_df = pl.read_csv(nids_filename)
    df = df.with_columns(
        nids_df["pred"].alias("nids_pred"),
    )

    # filter away data that was used for training
    df = df.filter(pl.col("nids_pred") >= 0)

    df, threshold = apply_quantile_threshold(df, 1-fpr)

    print(rf"Threshold at {fpr * 100}% FPR", threshold)

    block_rate_by_type = (
        df.filter(pl.col("label") != 0).group_by("type").agg(
            pl.mean("is_alert"),
            pl.mean("is_blocked_rule"),
            pl.mean("is_blocked_ai"),
        ).sort("type")
    )

    print(block_rate_by_type)

    x_range = np.arange(len(block_rate_by_type["type"]))

    plt.rc('text', usetex=True)

    plt.figure(figsize=(5, 4))
    plt.bar(
        x=x_range-0.3, 
        height=block_rate_by_type["is_alert"],
        width=0.3,
        color="#dddddd",
        edgecolor="k",
        hatch="x",
        label="TPR",
    )
    plt.bar(
        x=x_range, 
        height=block_rate_by_type["is_blocked_rule"],
        width=0.3,
        color="#72D686",
        edgecolor="k",
        hatch="o",
        label=r"CBR $\mathcal{R}_1$"
    )
    plt.bar(
        x=x_range+0.3, 
        height=block_rate_by_type["is_blocked_ai"],
        width=0.3,
        color="#f3c67a",
        alpha=0.8,
        edgecolor="k",
        hatch="*",
        label=r"CBR $\mathcal{R}_2$"
    )
    plt.xticks(x_range, block_rate_by_type["type"], rotation=90)
    plt.yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    plt.ylim(0, 1.2)
    plt.legend(ncol=3)
    plt.tight_layout()
    plt.savefig(f"fig/{nids_name}_blocked_by_type_{dataset_name}_fpr{fpr_pretty}.pdf")
    plt.draw()
    plt.show()
