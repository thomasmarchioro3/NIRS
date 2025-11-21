from __future__ import annotations
from contextvars import ContextVar
from typing import Optional, TypedDict

import polars as pl

from langchain_core.messages import BaseMessage 


CURRENT_RUNTIME = ContextVar("CURRENT_RUNTIME", default={})

class EvaluationResult(TypedDict):
    status: str
    cbr: float
    wbr: float

class Targets(TypedDict):
    cbr: float
    wbr: float


class RunTimeState(TypedDict, total=False):
    df: pl.DataFrame
    alert_window: pl.DataFrame         # alert flows window
    benign_window: pl.DataFrame        # benign flows window

    fpr: float                         # false-positive rate target or baseline
    update_time_ms: int                # update cadence for the agent (ms)
    seed: int                          # RNG seed for reproducibility

    last_rule: Optional[str]
    evaluation: EvaluationResult       # {"status": str, "cbr": float, "wbr": float}
    decision: str                      # "llm" or "end"
    decision_reason: str               # Human-readable reason
    targets: Targets                   # {"cbr": float, "wbr": float}
    attempts: int                         # retries in this decision cycle
    max_attempts: int                     # cap (e.g., 3)

class ChatState(TypedDict):
    messages: list[BaseMessage]
    runtime: RunTimeState
