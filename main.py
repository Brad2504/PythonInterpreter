# Main entry point for the Python interpreter

from lexer import Lexer
from parser import Parser
from eval import Evaluator
import readline
import os
import platform
import sys
import atexit

current_os = platform.system()

clear_arg = "cls" if current_os == "Windows" else "clear"

evaluator = Evaluator([])

history_file = "history.txt"

atexit.register(readline.write_history_file, history_file)

try:
    readline.read_history_file(history_file)
except FileNotFoundError:
    pass

readline.set_history_length(1000)

def run_code(code):
    tokens = Lexer(code).tokenize()
    ast = Parser(tokens).parse()
    evaluator.set_ast(ast)

    return evaluator.eval()

if __name__ == "__main__":
    while True:
        try:
            try:
                line = input("\033[34m" + ">>> " + "\033[0m")
            except KeyboardInterrupt:
                print("KeyboardInterrupt")
                continue

            if line.strip() == "exit":
                break

            if line.strip() == "clear":
                os.system(clear_arg)
                continue

            # If the line starts a block (ends with ':'), read subsequent
            # indented lines until a blank line is entered.
            if line.rstrip().endswith(":"):
                lines = [line]
                aborted = False
                while True:
                    try:
                        next_line = input("\033[34m" + "... " + "\033[0m")
                    except KeyboardInterrupt:
                        print("KeyboardInterrupt")
                        aborted = True
                        break

                    if next_line == "":
                        break

                    # Normalize leading groups of 4 spaces into tabs so the
                    # parser's TAB token is produced even when users indent
                    # with spaces.
                    leading_spaces = len(next_line) - len(next_line.lstrip(' '))
                    if leading_spaces > 0 and next_line.lstrip(' ')[0:1] != "\t":
                        if leading_spaces % 4 != 0:
                            raise RuntimeError("Indentation error: expected multiples of 4 spaces")
                        tabs = leading_spaces // 4
                        remainder = next_line.lstrip(' ')
                        next_line = "\t" * tabs + remainder

                    lines.append(next_line)

                if aborted:
                    continue

                code = "\n".join(lines) + "\n"
            else:
                code = line.lstrip() + "\n"
            
            code = code.encode().decode('unicode_escape')

            try:
                result = run_code(code)
            except KeyboardInterrupt:
                print("KeyboardInterrupt")
                continue

            if result is None:
                pass
            elif isinstance(result, list):
                if result and all(x is not None for x in result):
                    for result in result:
                        print(result)
            else:
                print(result)

        except Exception as e:
            print(f"Error: {e}")