"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.

Example usage:

python -m experiments.run_nids --dataset nb15 --seed 42
"""

import os
import sys

import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from nids.datasets import load_dataset


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="nb15")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    np.random.seed(args.seed)

    outdir = "results/temp/nids"

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    outfile = os.path.join(outdir, f"rf_{args.dataset}_seed{args.seed}_pred.csv")

    X_train, X_test, y_train, y_test = load_dataset(args.dataset, percent10=False)

    n_features = X_train.shape[1]

    n_train = len(X_train)
    n_test = len(X_test)

    model = RandomForestClassifier(
        n_estimators=100, 
        max_depth=10, 
        random_state=args.seed
    )

    print("Starting training.")

    model.fit(X_train, y_train)

    print(f"Saving results to {outfile}")

    y_pred = -np.ones(n_train + n_test)

    predicted_probs = model.predict_proba(X_test)
    assert isinstance(predicted_probs, np.ndarray)  # this line exists only to prevent complaits from the LSP

    y_pred[n_train:] = predicted_probs[:, 1]

    pd.DataFrame({"pred": y_pred}).to_csv(outfile, index=False)
