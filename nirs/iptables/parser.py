"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.
"""

import logging
import ipaddress

VALID_OPTIONS = ["-A"]  # allow only append
VALID_TABLES = ["FORWARD"]

# NOTE: These are all the protocols used in CIC-IDS 2017 and TON IoT
VALID_PROTOCOLS = ["tcp", "udp", "icmp", "hopopt"]
VALID_PROTOCOLS_WITH_PORTS = ["tcp", "udp"]

VALID_JUMPS = ["DROP"]  # allow only blocking actions


class InvalidIptablesRule(Exception):
    pass


def is_valid_ip(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def is_valid_ip_network(ip_network: str) -> bool:
    try:
        ipaddress.ip_network(ip_network, strict=False)
        return True
    except ValueError:
        return False

def is_valid_port(port: str) -> bool:
    try:
        int(port)
        return True
    except ValueError:
        return False

def is_valid_rule_dict(rule_dict: dict) -> bool:

    if rule_dict.get("option", None) not in VALID_OPTIONS:
        logging.debug("Invalid rule: Invalid/missing option")
        return False

    if rule_dict.get("table", None) not in VALID_TABLES:
        logging.debug("Invalid rule: Invalid/missing table")
        return False

    if rule_dict.get("src_ip", "any") != "any":
        src_ip = rule_dict["src_ip"]

        if not is_valid_ip(src_ip) and not is_valid_ip_network(src_ip):
            logging.debug(
                f"Invalid rule: Source IP '{rule_dict['src_ip']}' is not valid"
            )
            return False

    if rule_dict.get("dst_ip", "any") != "any":
        dst_ip = rule_dict["dst_ip"]

        if not is_valid_ip(dst_ip) and not is_valid_ip_network(dst_ip):
            logging.debug(
                f"Invalid rule: Destination IP '{rule_dict['dst_ip']}' is not valid"
            )
            return False

    if rule_dict.get("protocol", "any") != "any":
        protocol = rule_dict["protocol"]

        if protocol not in VALID_PROTOCOLS:
            logging.debug(f"Invalid rule: Protocol '{protocol}' is not valid")
            return False

    if rule_dict.get("src_port", "any") != "any":
        if rule_dict.get("protocol", "any") not in VALID_PROTOCOLS_WITH_PORTS:
            logging.debug(
                "Invalid rule: Source port cannot be specified without protocol"
            )
            return False
        src_port = rule_dict["src_port"]

        if not is_valid_port(src_port):
            logging.debug(
                f"Invalid rule: Source port '{rule_dict['src_port']}' is not valid"
            )
            return False

    if rule_dict.get("dst_port", "any") != "any":
        if rule_dict.get("protocol", "any") not in VALID_PROTOCOLS_WITH_PORTS:
            logging.debug(
                "Invalid rule: Source port cannot be specified without protocol"
            )
            return False
        dst_port = rule_dict["dst_port"]

        if not is_valid_port(dst_port):
            logging.debug(
                f"Invalid rule: Destination port '{rule_dict['dst_port']}' is not valid"
            )
            return False

    if rule_dict.get("jump", None) not in VALID_JUMPS:
        logging.debug("Invalid rule: Invalid/missing jump")
        return False

    return True


def parse_iptables_rule(rule: str) -> dict:
    """
    Simplified iptables rule parser.

    Allows only for the following iptables rules:
    -A INPUT -s <src_ip>[/<subnet>] -j DROP
    -A INPUT -d <src_ip>[/<subnet>] -p <protocol> -j DROP
    -A INPUT -d <dst_ip>[/<subnet>] -p <protocol> --dport <dst_port> -j DROP

    Args:
        rule (str): iptables rule, e.g. `-A INPUT -d 192.168.0.1/32 -p tcp -j DROP`
    """

    result = {
        "option": None,
        "table": None,
        "src_ip": "any",
        "dst_ip": "any",
        "protocol": "any",
        "src_port": "any",
        "dst_port": "any",
        "jump": None,
    }

    # Tokenize the rule
    tokens = rule.split()

    while len(tokens) > 0:
        token = tokens.pop(0)
        if token in VALID_OPTIONS:  # e.g., "-A"
            result["option"] = token
            table = tokens.pop(0)  # TABLE
            result["table"] = table
        match token:
            case "-s":
                result["src_ip"] = tokens.pop(0).removesuffix("/32")  # netmask /32 means one single host
            case "-d":
                result["dst_ip"] = tokens.pop(0).removesuffix("/32")  # netmask /32 means one single host
            case "-p":
                result["protocol"] = tokens.pop(0)
            case "--dport":
                result["dst_port"] = tokens.pop(0)
            case "-j":
                result["jump"] = tokens.pop(0)


    if not is_valid_rule_dict(result):
        raise InvalidIptablesRule

    return result