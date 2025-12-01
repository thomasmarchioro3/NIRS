# AgentNIRS: An LLM-driven agent for network intrusion response


![](./figures/fig/agentnirs.png)


Code for reproducing the paper "AgentNIRS: An LLM-Driven Agent for Network Intrusion Response" presented at WAITI (ACSAC 2025).

## Install dependencies

### Python dependencies

Using uv (recommended)

```sh
uv sync
```

### Ollama

Install [Ollama](https://ollama.com/) and run it on [http://localhost:11434](http://localhost:11434).
Pull the model to be used in the experiments.

```sh
ollama pull llama3.1:latest  # ID: 46e0c10c039e
```

## Run the code

1) Obtain predictions using NIDS random forest.

```sh
uv run -m nids.run_nids --dataset nb15 --fpr 1e-1 --seed 1
```
Repeat for seeds 1 to 5.

2) Run the NIRS evaluation script for `AgentNIRS` 

```sh
uv run -m experiments.run_nirs --dataset nb15 --fpr 1e-1 --nirs agent --llm_model llama3.1 --nids rf --seed 1
```
Repeat for seeds 1 ro 5 and for fpr 1e-4, 1e-3, 1e-2, 1e-1.

NOTE: Experiments using `AgentNIRS` can take a long time due to the multiple executions of the agent workflow.

After running an experiment, some new files will be created in `results/temp`:

```
results/temp
├── rf_nids_nb15_agentnirs_llama3_1_fpr_0_1_cbr0_wbr3_attempts5.csv
└── time_llama3_1_timestamp.csv
```

## Cite this paper

```bibtex
@inproceedings{saroui2025agentnirs,
  title={AgentNIRS: An LLM-Driven Agent for Network Intrusion Response},
  author={Rachida, Saroui and Thomas, Marchioro and Alexis, Olivereau},
  booktitle={2025 Annual Computer Security Applications Conference Workshops (ACSAC Workshops)},
  year={2025},
  organization={IEEE}
}
```