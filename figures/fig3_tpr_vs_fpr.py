"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.

Example usage:

```sh
python -m figures.fig3_tpr_vs_fpr --dataset nb15 --nids rf
```
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import recall_score

from nids.datasets import load_dataset, dataset_name_dict

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="nb15")
    parser.add_argument("--nids", type=str, default="rf")

    args = parser.parse_args()

    for seed in range(1, 6):
        filename = f"results/temp/nids/{args.nids}_{args.dataset}_seed{seed}_pred.csv"
        if not os.path.exists(filename):
            raise ValueError(f"File not found: {filename}")

    
    fpr_list = [1e-4, 1e-3, 1e-2, 1e-1]
    tpr_dict = {
        "mean": [],
        "std": [],
        "min": [],
        "max": [],
    }

    _, _, y_train, y_test = load_dataset(args.dataset, percent10=False)

    for fpr in fpr_list:

        tpr_list = []

        for seed in range(1, 6):
            filename = f"results/temp/nids/{args.nids}_{args.dataset}_seed{seed}_pred.csv"

            score_pred = pd.read_csv(filename)
            score_pred = score_pred[len(y_train):].fillna(0).to_numpy()

            threshold = np.quantile(score_pred[y_test == 0], 1-fpr)
            # print(rf"Threshold at {fpr*100:.2f}%:", threshold)

            y_pred = 1 * (score_pred > threshold)

            tpr = recall_score(y_test, y_pred)
            tpr_list.append(tpr)

        tpr_dict["mean"].append(np.mean(tpr_list))
        tpr_dict["std"].append(np.std(tpr_list))
        tpr_dict["min"].append(np.min(tpr_list))
        tpr_dict["max"].append(np.max(tpr_list))


    pd.DataFrame({
        "fpr": fpr_list, 
        "tpr_mean": tpr_dict["mean"], 
        "tpr_std": tpr_dict["std"],
        "tpr_min": tpr_dict["min"], 
        "tpr_max": tpr_dict["max"]
    }).to_csv(f"results/{args.nids}_{args.dataset}_tpr_vs_fpr.csv", index=False)

    plt.figure(figsize=(5, 3))
    plt.plot(fpr_list, tpr_dict["mean"], "s-", color="tab:gray")
    plt.fill_between(fpr_list, tpr_dict["min"], tpr_dict["max"], color="tab:gray", alpha=0.2)
    plt.xlabel("FPR cap")
    plt.ylabel("TPR")
    plt.xscale('log')
    plt.ylim(0, 1.1)
    plt.xlim(fpr_list[0], fpr_list[-1])
    plt.title(dataset_name_dict.get(args.dataset, str(args.dataset)))
    plt.savefig(f"figures/fig/{args.nids}_{args.dataset}_tpr_vs_fpr.pdf")
    plt.show()
