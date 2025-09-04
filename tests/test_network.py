"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.
"""

import unittest

from nirs.network import is_inter_subnet

class TestNetwork(unittest.TestCase):

    def test_is_inter_subnet(self):

        self.test_cases = [
            ("89.0.142.86", "244.178.44.111", True),
            ("89.0.142.86", "89.0.142.178", False),
            ("89.0.142.86", "244.178.44.111", True),
            ("237.84.2.86", "237.84.2.178", False),
            ("ff00::2e22::203a::ffff", "237.84.2.178", False),  # No support for IPv6
        ]

        for ip1, ip2, expected in self.test_cases:
            self.assertEqual(is_inter_subnet(ip1, ip2), expected)
