import time
from typing import Optional

import numpy as np
import polars as pl

from langchain_core.messages import HumanMessage
from langchain.chat_models import init_chat_model

from .config import CRITICAL_SUBNETS, DEFAULT_OLLAMA_MODEL, DEFAULT_TARGET_CBR, DEFAULT_TARGET_WBR
from .graph import build_graph
from .prompt import PROMPT_TEMPLATE
from .runtime import ChatState, RunTimeState
from .tools import build_tools

from ..base import WindowNIRS
from ...iptables import IptablesRule, InvalidIptablesRule

CRITICAL_SUBNETS_STR = " and ".join(str(subnet) for subnet in CRITICAL_SUBNETS)

def _make_agent_prompt(malicious_csv: str, benign_csv: str) -> str:

    return PROMPT_TEMPLATE.format(critical_subnets="59.166.0.0/24 and 149.171.126.0/24", malicious_csv=malicious_csv, benign_csv=benign_csv).strip()
    #return PROMPT_TEMPLATE_MISTRAL.format(critical_subnets="59.166.0.0/24 and 149.171.126.0/24", malicious_csv=malicious_csv, benign_csv=benign_csv).strip()

def update_ruleset_agentnirs(
    ruleset: list[IptablesRule],
    alert_window: pl.DataFrame,
    benign_window: pl.DataFrame,
    max_rules: int,
    llm,         # pre-initialized chat model
    graph,       # pre-built LangGraph graph
    num_examples: int,
    target_cbr: float=DEFAULT_TARGET_CBR,
    target_wbr: float=DEFAULT_TARGET_WBR,
    max_attempts: int=5,
) -> list[IptablesRule]:

    print("update_ruleset_agentnirs called")
    print("len alert window")
    print(len(alert_window))
    print("len benign window")
    print(len(benign_window))

    alert_df  = alert_window.with_columns(pl.Series(values=np.arange(len(alert_window)),  name="idx"))
    benign_df = benign_window.with_columns(pl.Series(values=np.arange(len(benign_window)), name="idx"))

    for rule in ruleset:
        idx_alert = rule.match_df(alert_df)
        if len(idx_alert) > 0:
            alert_df = alert_df.filter(~pl.col("idx").is_in(idx_alert))

        idx_benign = rule.match_df(benign_df)
        if len(idx_benign) > 0:
            benign_df = benign_df.filter(~pl.col("idx").is_in(idx_benign))

    cols = ["src_ip", "dst_ip", "protocol", "src_port", "dst_port", "src_data", "dst_data"]
    cols_alert_present  = [c for c in cols if c in alert_df.columns]
    cols_benign_present = [c for c in cols if c in benign_df.columns]

    alert_pd  = alert_df.select(cols_alert_present).tail(num_examples).to_pandas()   # type: ignore
    benign_pd = benign_df.select(cols_benign_present).tail(num_examples).to_pandas() # type: ignore

    full_prompt = _make_agent_prompt(alert_pd.to_csv(index=False), benign_pd.to_csv(index=False))

    print(full_prompt)

    runtime: RunTimeState = {
        "alert_window": alert_window,   
        "benign_window": benign_window, 
        "last_rule": None,
        "evaluation": {"status": "init", "cbr": 0.0, "wbr": 1.0},
        "decision": "llm",
        "decision_reason": "start",
        "targets": {"cbr": target_cbr, "wbr": target_wbr},
        "attempts": 0,
        "max_attempts": max_attempts,
    }

    initial_state: ChatState = {
        "messages": [HumanMessage(content=full_prompt)],
        "runtime": runtime,
    }

    final_state: ChatState = graph.invoke(initial_state, config={"recursion_limit": 20})

    rule_text: Optional[str] = final_state.get("runtime", {}).get("last_rule")

    print("rule_text:",rule_text)

    if not rule_text:
        return ruleset[-max_rules:] if len(ruleset) > max_rules else ruleset

    try:
        new_rule = IptablesRule(rule_text)
        print("new rule")
    except InvalidIptablesRule:
        print("invalid iptables rule")
        return ruleset[-max_rules:] if len(ruleset) > max_rules else ruleset

    if any(str(new_rule) == str(r) for r in ruleset):
        return ruleset[-max_rules:] if len(ruleset) > max_rules else ruleset

    ruleset.append(new_rule)
    if len(ruleset) > max_rules:
        ruleset = ruleset[-max_rules:]
    print("ruleset:",ruleset)
    return ruleset


class AgentNIRS(WindowNIRS):
    """
    NIRS agent.
    The agent graph and LLM are created once and reused.
    """

    def __init__(
        self,
        max_alert_window_idle_ms: int,
        max_alert_window_len_ms: int,
        benign_traffic_window_len_ms: int,
        df: pl.DataFrame,
        max_rules: int,
        model: str = DEFAULT_OLLAMA_MODEL,
        #model: str,
        num_examples_prompt: int = 10,
        target_cbr: float=DEFAULT_TARGET_CBR,
        target_wbr: float=DEFAULT_TARGET_WBR,
        max_attempts: int=5,
    ):
        super().__init__(
            max_alert_window_idle_ms,
            max_alert_window_len_ms,
            benign_traffic_window_len_ms,
            max_rules,
            #update_ruleset_fn=update_ruleset_agentnirs
        )

        self.iptables_status: Optional[str] = None
        self.model = model
        self.df = df
        #self.ollama_address = ollama_address
        self.num_examples_prompt = num_examples_prompt
        self.target_cbr = target_cbr
        self.target_wbr = target_wbr
        self.max_attempts = max_attempts

        self._llm = init_chat_model(self.model, model_provider="ollama")
        dummy_tools = build_tools(RunTimeState(df=None, last_rule=None, evaluation={}))
        self._graph = build_graph(
            self._llm.bind_tools(dummy_tools), 
            dummy_tools, 
            target_cbr=target_cbr, 
            target_wbr=target_wbr,
            max_attempts=max_attempts,
        )

        start_time = int(time.time() // 1)

        safe_model = self.model.replace(".", "_").replace(":", "_")
        self.time_file = f"results/temp/time_{safe_model}_{start_time}.csv"
        print(self.time_file)

        with open(self.time_file, "w") as f:
                f.write(f"time\n")

    def update(self, df: pl.DataFrame):
        benign_df = df.filter(pl.col("is_alert") == 0)
        alert_df = df.filter(pl.col("is_alert") == 1)

        print(alert_df)

        self.ingest_benign_df(benign_df)

        if len(alert_df) > 10:
            self.ingest_alert_df(alert_df)

            tic = time.perf_counter()
            self.ruleset = update_ruleset_agentnirs(
                self.ruleset,
                self.alert_window,
                self.benign_window,
                self.max_rules,
                llm=self._llm,
                graph=self._graph,
                num_examples=self.num_examples_prompt,
                target_cbr=self.target_cbr,
                target_wbr=self.target_wbr,
                max_attempts=self.max_attempts,
            )
            toc = time.perf_counter()


            with open(self.time_file, "a") as f:
                f.write(f"{toc - tic:.6f}\n")


            # update iptables status
            if len(self.ruleset) > 0:
                self.iptables_status = ""
                for rule in self.ruleset:
                    self.iptables_status += f"{str(rule)}\n"

        return
