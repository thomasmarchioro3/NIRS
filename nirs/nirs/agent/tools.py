from __future__ import annotations
import ipaddress
import json
import re
from typing import Literal, Optional

import numpy as np
import polars as pl
from langchain_core.runnables import Runnable
from langchain_core.tools import tool

from .config import CRITICAL_SUBNETS
from .runtime import RunTimeState, CURRENT_RUNTIME
from ...iptables import IptablesRule, InvalidIptablesRule, parse_iptables_rule


def rule_blocks_critical_subnet(rule: str) -> bool:
    """
    Checks whether the iptables rule blocks any critical subnet.
    """
    
    match = re.search(r"-s\s+([^\s]+)", rule)
    if not match:
        return False

    try:
        blocked = ipaddress.ip_network(match.group(1), strict=False)
        return any(blocked.overlaps(crit) for crit in CRITICAL_SUBNETS)
    except ValueError:
        pass

    match = re.search(r"-d\s+([^\s]+)", rule)
    if not match:
        return False

    try:
        blocked = ipaddress.ip_network(match.group(1), strict=False)
        return any(blocked.overlaps(crit) for crit in CRITICAL_SUBNETS)
    except ValueError:
        return False


def build_tools(runtime: RunTimeState, raw_llm: Optional[Runnable]=None):

    @tool
    def get_df_property(
        prop: Literal["len", "unique", "value_counts"],
        column: Optional[str] = None,
    ) -> str:
        """Inspect runtime df properties."""
        df = runtime["df"]

        match prop:
            case "len":
                return f"len(df): {len(df)}"
            case "unique":
                if column is None:
                    return "ERROR: column must be specified for unique()"
                return f"{column}.unique(): {df[column].unique()}"
            case "value_counts":
                if column is None:
                    return "ERROR: column must be specified for value_counts()"
                return f"{column}.value_counts(): {df[column].value_counts()}"
            case _:
                return "Unknown property"

    @tool
    def evaluate_rule(rule: str) -> str:
        """
    Evaluate an iptables rule:
    - Check validity
    - Check if it blocks critical subnets
    - Compute CBR and WBR within the runtime windows
    Returns a JSON string with fields: status, cbr, wbr.
        """
        print("evaluate_rule called")
        print("Received rule:", rule)

        if rule.strip().lower() == "none":
            return json.dumps({"status":"INVALID: Rule is 'none'", "cbr": 0.0, "wbr": 1.0})
        if rule_blocks_critical_subnet(rule):
            return json.dumps({"status":"INVALID: Rule blocks a critical subnet", "cbr": 0.0, "wbr": 1.0})

        try:
            rule_obj = IptablesRule(rule)
            print("Parsed rule successfully.")
        except InvalidIptablesRule:
            return json.dumps({"status":"INVALID: Rule syntax could not be parsed", "cbr":0.0, "wbr":1.0})

        rt = CURRENT_RUNTIME.get() or {}
        aw, bw = rt.get("alert_window"), rt.get("benign_window")

        if not isinstance(aw, pl.DataFrame): aw = pl.DataFrame(aw)
        if not isinstance(bw, pl.DataFrame): bw = pl.DataFrame(bw)
        if "idx" not in aw.columns: aw = aw.with_row_index("idx")
        if "idx" not in bw.columns: bw = bw.with_row_index("idx")

        print(f"Windows -> alerts:{aw.height}, benign:{bw.height}")

        def compute_blocked(df: pl.DataFrame) -> int:
            if df.is_empty():
                return 0
            blocked = rule_obj.match_df(df)
            return len(blocked)

        aw_blocked = compute_blocked(aw)
        bw_blocked = compute_blocked(bw)

        cbr = (aw_blocked / len(aw)) if len(aw) > 0 else 0.0
        print(f"CBR: {aw_blocked}/{len(aw)} = {cbr:.3f}")

        wbr = (bw_blocked / len(bw)) if len(bw) > 0 else 0.0
        print(f"CBR: {bw_blocked}/{len(bw)} = {cbr:.3f}")

        result = {"status":"VALID: Rule passed checks", "cbr":round(float(cbr),3), "wbr":round(float(wbr),3)}
        print("Evaluation result:", result)
        return json.dumps(result)


    return [evaluate_rule, get_df_property]
