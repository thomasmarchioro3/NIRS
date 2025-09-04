import os

import numpy as np

import polars as pl
import matplotlib.pyplot as plt

from nirs.datasets import load_dataset
from nirs.parse_args import get_args, get_resfile_name, get_nids_pred_filename

if __name__ == "__main__":


    args = get_args()

    nids_dir = "results/temp/nids"
    nirs_dir = "results/temp/nirs"

    dataset_name = args.dataset
    nirs_name = args.nirs

    fpr_list = [1e-4, 1e-3, 1e-2, 1e-1]

    eps = args.eps
    k_prompt = args.k_prompt
    update_time_ms = args.update_time_ms

    cbr_dict = {"mean": [], "std": [], "min": [], "max": []}
    wbr_dict = {"mean": [], "std": [], "min": [], "max": []}

    # for seed in range(1, 6):
    #     nidsfile = get_nidspredfile_name(args.nids, dataset_name, seed)
    #     nidsfile = os.path.join(nids_dir, nidsfile)
    #     print(nidsfile)
    #     assert os.path.isfile(nidsfile)

    for i, fpr in enumerate(fpr_list):
        for seed in range(1, 6):
            resfile = get_resfile_name(args.nids, dataset_name, nirs_name, fpr, eps, k_prompt, seed, update_time_ms)
            resfile = os.path.join(nirs_dir, resfile)
            print(resfile)
            assert os.path.isfile(resfile)

    eps_pretty = str(eps).replace(".", "_")
    df = load_dataset(name=dataset_name)
    df = df["label", "type"]

    for i, fpr in enumerate(fpr_list):
    
        cbr_list = []
        wbr_list = []

        for seed in range(1, 6):

            resfile = get_resfile_name(args.nids, dataset_name, nirs_name, fpr, eps, k_prompt, seed, update_time_ms)
            resfile = os.path.join(nirs_dir, resfile)

            res_df = pl.read_csv(resfile)

            df = df.with_columns(
                res_df["is_blocked"].alias("is_blocked"),
            )

            cbr = df.filter(pl.col("label") == 1)["is_blocked"].mean()
            wbr = df.filter(pl.col("label") == 0)["is_blocked"].mean()

            cbr_list.append(cbr)
            wbr_list.append(wbr)

        cbr_dict['mean'].append(np.mean(cbr_list))
        cbr_dict['std'].append(np.std(cbr_list))
        cbr_dict['min'].append(np.min(cbr_list))
        cbr_dict['max'].append(np.max(cbr_list))

        wbr_dict['mean'].append(np.mean(wbr_list))
        wbr_dict['std'].append(np.std(wbr_list))
        wbr_dict['min'].append(np.min(wbr_list))
        wbr_dict['max'].append(np.max(wbr_list))

    if nirs_name == "heuristic":
        outfile = f"results/{args.nids}_{dataset_name}_heuristicnirs_cbr_wbr_vs_fpr_eps{eps_pretty}.csv"
    else:
        outfile = f"results/{args.nids}_{dataset_name}_ollamanirs_cbr_wbr_vs_fpr.csv"

    df = pl.DataFrame(
        {
            "fpr": fpr_list,
            "cbr_mean": cbr_dict['mean'],
            "cbr_std": cbr_dict['std'],
            "cbr_min": cbr_dict['min'],
            "cbr_max": cbr_dict['max'],
            "wbr_mean": wbr_dict['mean'],
            "wbr_std": wbr_dict['std'],
            "wbr_min": wbr_dict['min'],
            "wbr_max": wbr_dict['max'],
        }
    )

    df.write_csv(outfile)

    plt.figure()
    plt.plot(fpr_list, cbr_dict['mean'], 's-', color="tab:green", label="CBR")
    plt.plot(fpr_list, wbr_dict['mean'], 's-', color="red", label="WBR")
    plt.xscale("log")
    plt.xlabel("FPR")
    plt.ylabel("Block rate")
    plt.legend()
    plt.grid(linestyle=":")
    plt.tight_layout()
    if nirs_name == "heuristic":
        plt.savefig(f"fig/heuristicnirs_cbr_wbr_vs_fpr_{dataset_name}.pdf")
    else:
        plt.savefig(f"fig/ollamanirs_cbr_wbr_vs_fpr_{dataset_name}_eps{eps_pretty}.pdf")

    plt.draw()

    plt.show()
