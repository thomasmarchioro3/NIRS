import numpy as np

import polars as pl
from sklearn.model_selection import train_test_split

if __name__ == "__main__":
    seed = 42
    np.random.seed(seed)

    df = pl.read_csv("data/nb15/nb15.csv", ignore_errors=True)
    df, _ = train_test_split(
        df,
        stratify=df["Label"],
        train_size=0.1,
        random_state=seed, 
    )

    df = df.sort("Stime") 
    df.write_csv("data/nb15/nb15_random10.csv")
