import unittest

from lexer import Lexer
from parser import Parser


class ParserTests(unittest.TestCase):
    def parse_expr(self, expr):
        tokens = Lexer(expr).tokenize()
        return Parser(tokens).parse()

    def test_less_than(self):
        self.assertEqual(
            self.parse_expr("1 < 2"),
            [(0, ("binop", "<", ("number", 1), ("number", 2)))],
        )

    def test_greater_than_or_equal(self):
        self.assertEqual(
            self.parse_expr("a >= 3"),
            [(0, ("binop", ">=", ("ident", "a"), ("number", 3)))],
        )

    def test_arithmetic_precedence_inside_comparison(self):
        self.assertEqual(
            self.parse_expr("1 + 2 * 3 == 7"),
            [
                (
                    0,
                    (
                        "binop",
                        "==",
                        ("binop", "+", ("number", 1), ("binop", "*", ("number", 2), ("number", 3))),
                        ("number", 7),
                    ),
                )
            ],
        )

    def test_parentheses(self):
        self.assertEqual(
            self.parse_expr("(1 + 2) * 3 > 8"),
            [
                (
                    0,
                    (
                        "binop",
                        ">",
                        ("binop", "*", ("binop", "+", ("number", 1), ("number", 2)), ("number", 3)),
                        ("number", 8),
                    ),
                )
            ],
        )

    def test_not_equal_identifiers(self):
        self.assertEqual(
            self.parse_expr("x != y"),
            [(0, ("binop", "!=", ("ident", "x"), ("ident", "y")))],
        )

    def test_invalid_expression_raises(self):
        with self.assertRaises(RuntimeError):
            self.parse_expr("1 <")

    def test_invalid_character_raises(self):
        with self.assertRaises(RuntimeError):
            self.parse_expr("1 $ 2")
    
    def test_nested_parentheses(self):
        self.assertEqual(
            self.parse_expr("1 * (2 + 3)"),
            [
                (
                    0,
                    (
                        "binop",
                        "*",
                        ("number", 1),
                        (
                            "binop",
                            "+",
                            ("number", 2),
                            ("number", 3)
                        )
                    )
                )
            ]
        )
    
    def test_logical_and_operator(self):
        self.assertEqual(
            self.parse_expr("a > 1 and b < 5"),
            [
                (
                    0,
                    (
                        "binop",
                        "and",
                        ("binop", ">", ("ident", "a"), ("number", 1)),
                        ("binop", "<", ("ident", "b"), ("number", 5))
                    )
                )
            ]
        )
    
    def test_logical_or_operator(self):
        self.assertEqual(
            self.parse_expr("x == 0 or y == 0"),
            [
                (
                    0,
                    (
                        "binop",
                        "or",
                        ("binop", "==", ("ident", "x"), ("number", 0)),
                        ("binop", "==", ("ident", "y"), ("number", 0))
                    )
                )
            ]
        )
    
    def test_inline_conditional_expression(self):
        self.assertEqual(
            self.parse_expr("1 if x > 0 else 2"),
            [
                (
                    0,
                    (
                        "inlinecond",
                        ("binop", ">", ("ident", "x"), ("number", 0)),
                        ("number", 1),
                        ("number", 2)
                    )
                )
            ]
        )

    def test_leading_tabs_are_recorded_as_indent(self):
        self.assertEqual(
            self.parse_expr("\t\t1 + 2"),
            [(2, ("binop", "+", ("number", 1), ("number", 2)))],
        )

    def test_multiline_nested_if_parses_with_indents(self):
        self.assertEqual(
            self.parse_expr(
                "if x > 0:\n\tif y > 0:\n\t\t1\n\telse:\n\t\t2"
            ),
            [
                (0, ("if", ("binop", ">", ("ident", "x"), ("number", 0)))),
                (1, ("if", ("binop", ">", ("ident", "y"), ("number", 0)))),
                (2, ("number", 1)),
                (1, ("else", None)),
                (2, ("number", 2)),
            ],
        )
    
    def test_multiline_conditional_expression(self):
        self.assertEqual(
            self.parse_expr(
                "if x > 0:\n\t3\n\t4\nelif x < 0:\n\t5\n\t6\nelse:\n\t7\n\t8"
            ),
            [
                (0, ("if", ("binop", ">", ("ident", "x"), ("number", 0)))),
                (1, ("number", 3)),
                (1, ("number", 4)),
                (0, ("elif", ("binop", "<", ("ident", "x"), ("number", 0)))),
                (1, ("number", 5)),
                (1, ("number", 6)),
                (0, ("else", None)),
                (1, ("number", 7)),
                (1, ("number", 8)),
            ]
        )

    def test_unmatched_parenthesis_raises(self):
        with self.assertRaises(RuntimeError):
            self.parse_expr("(1 + 2")

    def test_string_concatenation_parses(self):
        self.assertEqual(
            self.parse_expr('"hello" + \'world\''),
            [
                (
                    0,
                    (
                        "binop",
                        "+",
                        ("string", "hello"),
                        ("string", "world"),
                    ),
                )
            ],
        )

if __name__ == "__main__":
    unittest.main()
