import unittest

from pyinterp.eval import Evaluator
from pyinterp.lexer import Lexer
from pyinterp.parser import Parser


class EvaluatorTests(unittest.TestCase):
    def eval_code(self, code):
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()
        return Evaluator(ast).eval()

    def test_multiline_if_uses_tabs_to_group_body(self):
        self.assertEqual(
            self.eval_code(
                "if 1 < 2:\n\t10\n\t20\nelif 2 < 1:\n\t30\nelse:\n\t40\n\t50"
            ),
            [10, 20],
        )

    def test_multiline_else_branch_runs_when_if_is_false(self):
        self.assertEqual(
            self.eval_code(
                "if 1 > 2:\n\t10\n\t20\nelif 2 < 1:\n\t30\nelse:\n\t40\n\t50"
            ),
            [40, 50],
        )

    def test_inline_conditional_expression_evaluates(self):
        self.assertEqual(self.eval_code("1 if 2 > 1 else 3"), 1)

    def test_top_level_expressions_still_evaluate_in_order(self):
        self.assertEqual(self.eval_code("1\n2 + 3\n4 * 5"), [1, 5, 20])

    def test_nested_multiline_if_evaluates_inner_branch(self):
        self.assertEqual(
            self.eval_code(
                "if 1 < 2:\n\tif 2 < 3:\n\t\t100\n\telse:\n\t\t200\nelse:\n\t300"
            ),
            100,
        )

    def test_false_multiline_if_skips_all_branches(self):
        self.assertEqual(
            self.eval_code(
                "if 1 > 2:\n\t10\nelif 2 > 3:\n\t20\nelse:\n\t30\n\t40"
            ),
            [30, 40],
        )

    def test_indentation_error_when_if_body_is_not_indented(self):
        with self.assertRaises(RuntimeError):
            self.eval_code("if 1 < 2:\n10")

    def test_indentation_error_on_unexpected_extra_indent(self):
        with self.assertRaises(RuntimeError):
            self.eval_code("if 1 < 2:\n\t10\n\t\t20")

    def test_indentation_error_when_elif_has_no_indented_body(self):
        with self.assertRaises(RuntimeError):
            self.eval_code("if 1 > 2:\n\t10\nelif 2 < 3:\n20")

    def test_function_definition_and_call_returns_value(self):
        self.assertEqual(
            self.eval_code(
                "def add(a, b)\n\treturn a + b\nadd(4, 2)"
            ),
            6,
        )

    def test_function_call_still_works_after_replacing_ast(self):
        evaluator = Evaluator([])

        tokens = Lexer("def add(a, b)\n\treturn a + b").tokenize()
        evaluator.set_ast(Parser(tokens).parse())
        evaluator.eval()

        tokens = Lexer("add(4, 2)").tokenize()
        evaluator.set_ast(Parser(tokens).parse())

        self.assertEqual(evaluator.eval(), 6)
    
    def test_variable_assignment_and_usage(self):
        self.assertEqual(
            self.eval_code(
                "x = 5"
            ),
            None,
        )

    def test_tuple_assignment_unpacks_values(self):
        self.assertEqual(
            self.eval_code(
                "a, b = (1, 2)\na + b"
            ),
            [None, 3],
        )

    def test_for_loop_unpacks_tuple_targets(self):
        self.assertEqual(
            self.eval_code(
                "for a, b in [(1, 2), (3, 4)]:\n\ta + b"
            ),
            [3, 7],
        )

    def test_string_concatenation_evaluates(self):
        self.assertEqual(self.eval_code('"hello" + \'world\''), "helloworld")


if __name__ == "__main__":
    unittest.main()