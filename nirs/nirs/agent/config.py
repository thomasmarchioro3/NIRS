# TODO: Use configparse and an `agent_config.ini` file to config these variables

import ipaddress


CRITICAL_SUBNETS = [
    ipaddress.ip_network("59.166.0.0/24"),
    ipaddress.ip_network("149.171.126.0/24"),
]

DEFAULT_OLLAMA_MODEL = "llama3.1:8b"
# DEFAULT_OLLAMA_MODEL = "mistral:latest"
# DEFAULT_OLLAMA_MODEL = "gpt-oss:latest"
# DEFAULT_OLLAMA_MODEL = "deepseek-r1:8b"
# DEFAULT_OLLAMA_MODEL = "qwen3:8b"


DEFAULT_TARGET_CBR = 0.30
DEFAULT_TARGET_WBR = 1.00
