"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.
"""

import ipaddress

protocol_numbers = {
    "hopopt": 0,
    "icmp": 1,
    "igmp": 2,
    "ggp": 3,
    "ipv4": 4,
    "tcp": 6,
    "egp": 8,
    "igp": 9,
    "udp": 17,
    "gre": 47,
    "esp": 50,
    "ah": 51,
    "ipv6-icmp": 58,
    "sctp": 132,
    "udplite": 136
}


inv_protocol_numbers = {v: k for k, v in protocol_numbers.items()}

def is_inter_subnet(ip1: str, ip2: str):
    """
    Assuming /24, check if ip1 and ip2 are in different subnets.
    For IPv6, always return False.
    """
    try:
        ip1_ = ipaddress.IPv4Address(ip1)
        ipaddress.IPv4Address(ip2)
    except ValueError:
        return False
    return ip1_ not in ipaddress.IPv4Network(ip2+'/24', strict=False)

