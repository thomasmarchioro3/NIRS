"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.
"""

import json
import requests

import numpy as np
import pandas as pd

SYSTEM_PROMPT_TEMPLATE = r"""
You are a network security engineer. You are tasked with monitoring incoming malicious and benign traffic, and writing one iptables rule accordingly. 
You will observe examples of benign flows and malicious flows. You will also have access to the current iptables status. 
Based on this information, you will write one single iptables rule, which should be enclosed within <rule></rule> tags. 

Valid formats for the rule include:
{{accepted_formats}}

The /<subnet> is optional.

Examples of valid rules:
{{few_shot_examples}}

"""

ACCEPTED_FORMATS = [
    "-A FORWARD -s <src_ip>/<subnet> -j DROP",
    "-A FORWARD -d <dst_ip>/<subnet> -j DROP",
    "-A FORWARD -d <dst_ip>/<subnet> -p <protocol> -j DROP",
    "-A FORWARD -d <dst_ip>/<subnet> -p <protocol> --dport <dst_port> -j DROP",
]

FEW_SHOT_IPTABLES = [
    "-A FORWARD -s 10.25.0.41 -j DROP",
    "-A FORWARD -s 172.21.0.1/24 -j DROP",
    "-A FORWARD -d 208.42.13.2 -j DROP",
    "-A FORWARD -d 113.0.201.5 -p icmp",
    "-A FORWARD -d 32.153.41.11 -p tcp --dport 22",
]

USER_PROMPT_TEMPLATE = r"""
Malicious flows:
{{malicious_flows}}

Benign flows:
{{benign_flows}}

Iptables status:
{{iptables_status}}

Output only one iptables DROP rule to append to the FORWARD table, enclosed within <rule></rule> tags.
The rule must block most of the malicious flows and must not block most of the benign flows.
Keep your response short.
"""

DEFAULT_IPTABLES_STATUS = """
[Empty]
"""

def make_system_prompt(use_template: str="default"):
    template = SYSTEM_PROMPT_TEMPLATE
    match use_template:
        case "default":
            template = SYSTEM_PROMPT_TEMPLATE
        case _:
            raise ValueError

    accepted_formats_str = "\n".join(f"<rule>{rule}</rule>" for rule in ACCEPTED_FORMATS)
    few_shot_str = "\n".join(f"<rule>{rule}</rule>" for rule in FEW_SHOT_IPTABLES)
    system_prompt = template.replace(
        "{{accepted_formats}}", accepted_formats_str
    ).replace("{{few_shot_examples}}", few_shot_str)
    
    return system_prompt

def make_user_prompt(malicious_flows: pd.DataFrame, benign_flows: pd.DataFrame, iptables_status: str | None=None):

    if iptables_status is None:
        iptables_status = DEFAULT_IPTABLES_STATUS

    template = USER_PROMPT_TEMPLATE

    user_prompt = template.replace(
        r"{{benign_flows}}", benign_flows.to_csv(index=False)
    ).replace(
        r"{{malicious_flows}}", malicious_flows.to_csv(index=False)
    ).replace(
        r"{{iptables_status}}", iptables_status
    )
    
    return user_prompt


def decode_response(response: requests.Response):

    res = response.text
    res = json.loads(res)
    message = res.get("message", None)

    if message is None:
        return ""

    if message["role"] != "assistant":
        return ""

    content = message.get("content", "")
    return content