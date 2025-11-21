"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.
"""

from .nirs.base import BaseNIRS, WindowNIRS
from .nirs.heuristic import HeuristicNIRS
from .nirs.llm import OllamaNIRS
from .nirs.agent import AgentNIRS
