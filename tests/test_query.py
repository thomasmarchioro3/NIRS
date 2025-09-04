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

from nirs.ollama.query import extract_rule_from_answer


class TestParseRule(unittest.TestCase):

    def test_parse_rule(self):

        self.test_cases = [
            {
                "input": """
                Lorem ipsum.

                <rule>OK</rule>

                Dolor sit amet something I don't know latin.

                """,
                "expected": "OK",
            },
            {
                "input": """
                Lorem ipsum.

                <rule> OK   </rule>

                Dolor sit amet something I don't know latin.
                """,
                "expected": "OK",
            },
            {
                "input": """
                Lorem ipsum.

                <rule>OK</rule>
                <rule>NOT OK :( </rule>

                Dolor sit amet something I don't know latin.
                """,
                "expected": "OK",
            },
            {
                "input": """
                Lorem ipsum.

                <rule>  -A FORWARD -d 10.2.0.3 -j DROP</rule>

                Dolor sit amet something I don't know latin.

                <rule>-A FORWARD -s 10.2.0.4 -j DROP</rule>

                Non sequitur.
                """,
                "expected": "-A FORWARD -d 10.2.0.3 -j DROP",
            },
        ]

        for test_case in self.test_cases:
            answer = test_case["input"]
            logging.debug(answer)
            expected = test_case["expected"]
            output = extract_rule_from_answer(answer)
            self.assertEqual(output, expected)

    def test_error(self):
        # Verify that IndexError is raised when the answer contains no rule.

        answer = """
            Lorem ipsum.
            """
        try:

            extract_rule_from_answer(answer)
        except IndexError:
            return

        self.fail("IndexError not raised")

if __name__ == "__main__":

    unittest.main()
