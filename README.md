# Network Intrusion Response Systems (NIRS)

This code allows to evaluate Network Intrusion Response Systems based on iptables rules.
A Network Intrusion Response Systems (NIRS) uses alerts from Network Intrusion Detection
Systems (NIDS) to dynamically generate firewall rules. 
More details can be found in the paper.

## Create and evaluate a custom NIRS

Create a NIRS class by extending the BaseNIRS class:

```python
from src.nirs import BaseNIRS

class MyNIRS(BaseNIRS):

    def __init__(self, ...) -> None:
        # implement constructor

    def apply_rules(self, df: pl.DataFrame) -> np.ndarray:
        # implement the logic for applying firewall rules to network flows
        # to a DataFrame of network flows (this function should return the
        # indexes of the blocked flows)
        idx_blocked = ...
        return idx_blocked

    def update(self, df: pl.DataFrame) -> None
        # implement your logic for ingesting a DataFrame of network flows
        # and updating the firewall rules

my_nirs = MyNIRS(...)
```

and evaluate it using the `eval_nirs` function.

```python
from src.eval import eval_nirs

df = ...  # Polars DataFrame of labeled network flows 

eval_nirs(
    df = df,
    nirs = my_nirs,
    update_time_ms = 30_000,  # call my_nirs.update(...) every 30s, tweak this value depending on your use case
    seed = 42,
)
```

## Run the code

#### Using a Python virtual environment or Conda environment

1) Activate the environment: you should see `(env_name)` on your shell.

2) Install dependencies

```sh
pip install -r requirements.txt
```

3) Run scripts as modules as specified in their description.
For example, to run `experiments/run_nirs.py`

```sh
python -m experiments.run_nirs --help
```

#### Using uv

```sh
uv sync
```

## Reproduce the paper's results

#### Download the NB15 dataset

The dataset is available [here](https://research.unsw.edu.au/projects/unsw-nb15-dataset)

Download `UNSW-NB15_1.csv`,...,`UNSW-NB15_4.csv` and merge them into a single file `nb15.csv`.
The CSV file should be located at `data/nb15/nb15.csv`

#### Run NIRS with ideal NIDS (perfect NIDS predictions)

1) Run `HeuristicNIRS` with ideal NIDS

```sh
python -m src.run_nirs --dataset nb15 --nirs heuristic --nids ideal
```

2) Run `OllamaNIRS` with ideal NIDS (*requires [Ollama](https://ollama.com/) to be installed and running on* [http://localhost:11434](http://localhost:11434))

```sh
python -m src.run_nirs --dataset nb15 --nirs ollama --nids ideal
```

#### Run NIRS with real NIDS (random forest classifier)

1) Obtain predictions using NIDS random forest.

```sh
python -m src.run_nids --dataset nb15 --fpr 1e-1 --seed 1
```
Repeat for seeds 1 to 5.

2) Run the NIRS evaluation script for `HeuristicNIRS` 

```sh
python -m src.run_nirs --dataset nb15 --fpr 1e-1 --nirs heuristic --nids ideal
```
and `OllamaNIRS`
```sh
python -m src.run_nirs --dataset nb15 --fpr 1e-1 --nirs heuristic --nids ideal
```
Repeat for seeds 1 ro 5 and for fpr 1e-4, 1e-3, 1e-2, 1e-1.

Your `results` directory should look as follows.

```sh
├── results
│   ├── rf_nb15_tpr_vs_fpr.csv
│   └── temp
│       ├── nids
│       │   ├── rf_nb15_seed1_pred.csv
│       │   ├── rf_nb15_seed2_pred.csv
│       │   ├── rf_nb15_seed3_pred.csv
│       │   ├── rf_nb15_seed4_pred.csv
│       │   └── rf_nb15_seed5_pred.csv
│       ├── rf_nids_nb15_heuristicnirs_fpr0_1_update_1800000_seed1.csv
│       ├── rf_nids_nb15_heuristicnirs_fpr0_1_update_1800000_seed2.csv
│       ├── rf_nids_nb15_heuristicnirs_fpr0_1_update_1800000_seed3.csv
│       ├── rf_nids_nb15_heuristicnirs_fpr0_1_update_1800000_seed4.csv
│       └── rf_nids_nb15_heuristicnirs_fpr0_1_update_1800000_seed5.csv
...
```

## Cite this project

```
@inproceedings{marchioro2025network,
  title={Network Intrusion Response Systems: Towards standardized evaluation of intrusion response},
  author={Marchioro, Thomas and Saroui, Rachida and Olivereau, Alexis},
  booktitle={International Workshop on Assessment with New methodologies, Unified Benchmarks, and environments, of Intrusion detection and response Systems},
  pages={},
  year={2025},
  organization={Springer}
}
```
