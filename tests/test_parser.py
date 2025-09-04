"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.
"""

import unittest
import logging

from nirs.iptables.parser import parse_iptables_rule


class TestIptablesParser(unittest.TestCase):

    def test_parser(self):

        test_cases = [
            {
                "FORWARD": "-A FORWARD -d 192.168.0.1/32 -p tcp -j DROP",
                "expected": {
                    "option": "-A",
                    "table": "FORWARD",
                    "src_ip": "any",
                    "dst_ip": "192.168.0.1",
                    "protocol": "tcp",
                    "src_port": "any",
                    "dst_port": "any",
                    "jump": "DROP",
                },
            },
            {
                "FORWARD": "-A FORWARD -s 10.0.0.0/8 -p udp --dport 53 -j DROP",
                "expected": {
                    "option": "-A",
                    "table": "FORWARD",
                    "src_ip": "10.0.0.0/8",
                    "dst_ip": "any",
                    "protocol": "udp",
                    "src_port": "any",
                    "dst_port": "53",
                    "jump": "DROP",
                },
            },
            {
                "FORWARD": "-A FORWARD -d 8.8.8.8 -p icmp -j DROP",
                "expected": {
                    "option": "-A",
                    "table": "FORWARD",
                    "src_ip": "any",
                    "dst_ip": "8.8.8.8",
                    "protocol": "icmp",
                    "src_port": "any",
                    "dst_port": "any",
                    "jump": "DROP",
                },
            },
            {
                "FORWARD": "-A FORWARD -s 172.16.0.0/16 -p tcp --dport 21 -j DROP",
                "expected": {
                    "option": "-A",
                    "table": "FORWARD",
                    "src_ip": "172.16.0.0/16",
                    "dst_ip": "any",
                    "protocol": "tcp",
                    "src_port": "any",
                    "dst_port": "21",
                    "jump": "DROP",
                },
            },
        ]

        for test_case in test_cases:
            rule = test_case["FORWARD"]
            expected_dict = test_case["expected"]
            rule_dict = parse_iptables_rule(rule)
            logging.debug(f"Rule: {rule}")
            logging.debug(f"Expected: {expected_dict}")
            logging.debug(f"Actual: {rule_dict}")

            self.assertDictEqual(rule_dict, expected_dict)

