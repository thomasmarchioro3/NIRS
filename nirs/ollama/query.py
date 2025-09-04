"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.
"""

import json
import logging
import re
import time

import requests

from .prompt import decode_response


def run_query_ollama(
    model: str,
    system_prompt: str,
    user_prompt: str,
    ollama_address: str="http://localhost:11434",
    num_ctx: int=1024,
    temperature: int=0,
    seed: int=42,
    ):

    """
    Send a query to the Ollama AI chatbot.

    Args:
        model: The model name to use for the query.
        system_prompt: The system prompt to pass to Ollama.
        user_prompt: The user prompt to pass to Ollama.
        ollama_address: The address of the Ollama server, defaults to http://localhost:11434/api/chat.
        num_ctx: The number of context tokens to use for the query, defaults to 1024.
        temperature: The temperature to use for the query, defaults to 0.
        seed: The random seed to use for the query, defaults to 42.

    Returns:
        The answer from Ollama.

    Raises:
        requests.exceptions.ConnectionError if the query cannot be sent to Ollama, e.g. if Ollama is not running.
    """

    chat_api_address = f"{ollama_address}/api/chat"

    try:
        tic = time.perf_counter()
        response = requests.post(
            chat_api_address,
            headers={"Content-Type": "application/json"},
            data=json.dumps({
                "model": model,
                "stream": False,
                "options": {
                    "temperature": 0,
                    "seed": seed,
                    "num_ctx": num_ctx
                },
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            })
        )

        toc = time.perf_counter()
        logging.info(f"Query to Ollama took {toc - tic:0.4f} seconds")

        # print(response.text)
        answer = decode_response(response) 

        logging.debug(user_prompt)
        logging.debug(answer)

    except requests.exceptions.ConnectionError as e:
        logging.error("Cannot connect to Ollama. Verify that Ollama is running with the specified model. Connection error:", e)
        answer = ""
        exit()

    return answer


def extract_rule_from_answer(answer: str):
    """
    Extracts the iptables rule from the given answer string.

    The function searches for a rule enclosed within <rule></rule> tags in the 
    provided answer string. It returns the first matched rule as a stripped string.

    Args:
        answer (str): The string containing the iptables rule enclosed in <rule></rule> tags.

    Returns:
        str: The extracted iptables rule.
    """

    matches = re.findall(r"<rule>(.*?)</rule>", answer, re.DOTALL)
    rule = matches[0].strip()

    return rule