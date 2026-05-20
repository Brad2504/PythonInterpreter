import unittest

from pyinterp.lexer import Lexer


class LexerTests(unittest.TestCase):
    def test_tokenizes_numbers_and_operators(self):
        self.assertEqual(
            Lexer("1 + 2 * 3 == 7").tokenize(),
            [
                ("NUMBER", 1),
                ("OP", "+"),
                ("NUMBER", 2),
                ("OP", "*"),
                ("NUMBER", 3),
                ("OP", "=="),
                ("NUMBER", 7),
            ],
        )

    def test_tokenizes_conditionals_and_colons(self):
        self.assertEqual(
            Lexer("if x > 0:\nelse:").tokenize(),
            [
                ("CONDITIONAL", "if"),
                ("IDENT", "x"),
                ("OP", ">"),
                ("NUMBER", 0),
                ("COLON", ":"),
                ("NEWLINE", "\n"),
                ("CONDITIONAL", "else"),
                ("COLON", ":"),
            ],
        )

    def test_preserves_tab_indentation(self):
        self.assertEqual(
            Lexer("if x:\n\t1\n\t\t2").tokenize(),
            [
                ("CONDITIONAL", "if"),
                ("IDENT", "x"),
                ("COLON", ":"),
                ("NEWLINE", "\n"),
                ("TAB", "\t"),
                ("NUMBER", 1),
                ("NEWLINE", "\n"),
                ("TAB", "\t"),
                ("TAB", "\t"),
                ("NUMBER", 2),
            ],
        )

    def test_tokenizes_single_and_double_quoted_strings(self):
        self.assertEqual(
            Lexer('"hello" + \'world\'').tokenize(),
            [
                ("DOUBLEQUOTE", '"hello"'),
                ("OP", "+"),
                ("SINGLEQUOTE", "'world'"),
            ],
        )


if __name__ == "__main__":
    unittest.main()