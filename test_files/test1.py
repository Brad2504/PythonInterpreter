from pyinterp.lexer import Lexer
from pyinterp.parser import Parser
from pyinterp.eval import Evaluator

def eval_code(code):
    tokens = Lexer(code).tokenize()
    ast = Parser(tokens).parse()
    return Evaluator(ast).eval()

print(eval_code("print('hello world')"))