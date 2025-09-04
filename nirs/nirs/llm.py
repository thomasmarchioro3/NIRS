"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.
"""

import numpy as np
import polars as pl

from .base import WindowNIRS

from nirs.iptables import IptablesRule, InvalidIptablesRule

from nirs.ollama.query import run_query_ollama, extract_rule_from_answer
from nirs.ollama.prompt import make_system_prompt, make_user_prompt



def _update_ruleset(
    ruleset: list,
    alert_df: pl.DataFrame,
    benign_df: pl.DataFrame,
    max_rules: int,
    model: str,
    num_examples: int,
    system_prompt: str | None = None,
    ollama_address: str = "http://localhost:11434",
    iptables_status: str | None = None,
):
    assert system_prompt is not None

    # apply current ruleset first (avoids repeating rules)
    alert_df = alert_df.with_columns(
        pl.Series(values=np.arange(len(alert_df)), name="idx")
    )
    benign_df = benign_df.with_columns(
        pl.Series(values=np.arange(len(benign_df)), name="idx")
    )
    for rule in ruleset:
        idx_blocked_alert = rule.match_df(alert_df)
        alert_df = alert_df.filter(~pl.col("idx").is_in(idx_blocked_alert))
        idx_blocked_benign = rule.match_df(benign_df)
        benign_df = benign_df.filter(~pl.col("idx").is_in(idx_blocked_benign))

    alert_df = (
        alert_df[["src_ip", "dst_ip", "protocol", "src_port", "dst_port", "src_data", "dst_data"]]
        .tail(num_examples)
        .to_pandas()
    )  # type: ignore
    benign_df = (
        benign_df[["src_ip", "dst_ip", "protocol", "src_port", "dst_port", "src_data", "dst_data"]]
        .tail(num_examples)
        .to_pandas()
    )  # type: ignore

    user_prompt = make_user_prompt(alert_df, benign_df, iptables_status)  # type: ignore

    answer = run_query_ollama(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        ollama_address=ollama_address,
    )

    try:
        rule_str = extract_rule_from_answer(answer)
    except IndexError:
        print("Failed to extract rule from answer")
        return ruleset

    try:
        rule = IptablesRule(rule_str)
        print(rule)

        # Do not add rule if it exists already
        if str(rule) in [str(r) for r in ruleset]:
            return ruleset
        ruleset.append(rule)
    except InvalidIptablesRule as e:
        print(f"Failed to add rule to ruleset: {e}")
        pass


    if len(ruleset) > max_rules:
        return ruleset[-max_rules:]
    return ruleset


class OllamaNIRS(WindowNIRS):
    def __init__(
        self,
        max_alert_window_idle_ms: int,
        max_alert_window_len_ms: int,
        benign_traffic_window_len_ms: int,
        max_rules: int,
        model: str = "llama3:8b",
        num_examples_prompt: int = 10,
        ollama_address: str = "http://localhost:11434",
    ):
        super().__init__(
            max_alert_window_idle_ms,
            max_alert_window_len_ms,
            benign_traffic_window_len_ms,
            max_rules,
            update_ruleset_fn=_update_ruleset,
        )

        self.iptables_status = None

        self.system_prompt = make_system_prompt()

        self.model = model
        self.ollama_address = ollama_address
        self.num_examples_prompt = num_examples_prompt

    def update(self, df: pl.DataFrame):
        benign_df = df.filter(pl.col("is_alert") == 0)
        alert_df = df.filter(pl.col("is_alert") == 1)

        self.ingest_benign_df(benign_df)

        if len(alert_df) > 0:
            self.ingest_alert_df(alert_df)
            self.ruleset = _update_ruleset(
                self.ruleset,
                self.alert_window,
                self.benign_window,
                self.max_rules,
                model=self.model,
                ollama_address=self.ollama_address,
                num_examples=self.num_examples_prompt,
                system_prompt=self.system_prompt,
                iptables_status=self.iptables_status,
            )

            # update iptables status
            if len(self.ruleset) > 0:
                self.iptables_status = ""
                for rule in self.ruleset:
                    self.iptables_status += f"{str(rule)}\n"

        return

