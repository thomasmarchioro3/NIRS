"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.
"""

import logging
import unittest

import polars as pl

from nirs.iptables.parser import parse_iptables_rule
from nirs.iptables.match import match_rule_df

from nirs.iptables.rule import IptablesRule


class TestMatchRule(unittest.TestCase):
    
    def setUp(self):

        data = [
            {
                "idx": 0,
                "timestamp": 1,
                "src_ip": "1.1.1.1",
                "dst_ip": "2.2.2.2",
                "src_port": 80,
                "dst_port": 80,
                "protocol": "tcp",
                "src_data": 1,
                "dst_data": 2
            },

            {
                "idx": 1,
                "timestamp": 2,
                "src_ip": "3.3.3.3",
                "dst_ip": "4.4.4.4",
                "src_port": 1000,
                "dst_port": 3000,
                "protocol": "tcp",
                "src_data": 3,
                "dst_data": 4
            },

            {
                "idx": 2,
                "timestamp": 3,
                "src_ip": "172.16.0.1",
                "dst_ip": "172.16.0.2",
                "src_port": 22,
                "dst_port": 22,
                "protocol": "tcp",
                "src_data": 5,
                "dst_data": 6
            },

            {
                "idx": 3,
                "timestamp": 4,
                "src_ip": "172.16.0.3",
                "dst_ip": "172.16.0.4",
                "src_port": 22,
                "dst_port": 22,
                "protocol": "tcp",
                "src_data": 7,
                "dst_data": 8
            }
        ]

        self.rules_str = [
            "-A FORWARD -d 172.16.0.1/32 -p tcp --dport 22 -j DROP",
            "-A FORWARD -d 172.16.0.1/16 -p tcp -j DROP",
        ]


        self.expected = [
            [2],
            [2, 3],
        ]

        self.X = pl.DataFrame(data)
    
    def test_match_rule_df(self):
        
        rule = parse_iptables_rule(self.rules_str[0])
        logging.debug(rule)
        result = match_rule_df(self.X, rule)
        logging.debug(result)
        self.assertEqual(result.tolist(), [2])

        rule = parse_iptables_rule(self.rules_str[1])
        logging.debug(rule)
        result = match_rule_df(self.X, rule)
        logging.debug(result)
        self.assertEqual(result.tolist(), [2, 3])


    def test_match_iptables_rule(self):

        for rule_str, expected in zip(self.rules_str, self.expected):
            rule = IptablesRule(rule_str)
            result = rule.match_df(self.X).tolist()
            self.assertEqual(result, expected)



if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")
    handler = logging.StreamHandler()
    unittest.main()