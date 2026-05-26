# Main entry point for the Python interpreter

from pyinterp.lexer import Lexer
from pyinterp.parser import Parser
from pyinterp.eval import Evaluator
import readline
import os
import platform
import sys
import atexit
import argparse
import pytest
from pathlib import Path

MAIN_PROMPT = "\x01\033[1;35m\x02>>>\x01\033[0m\x02 "
CONT_PROMPT = "\x01\033[1;35m\x02...\x01\033[0m\x02 "
HISTORY_FILE = os.path.expanduser("~/.pyinterp_history")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_DIR = PROJECT_ROOT / "tests"

current_os = platform.system()

clear_arg = "cls" if current_os == "Windows" else "clear"

evaluator = Evaluator([])

atexit.register(readline.write_history_file, HISTORY_FILE)

try:
    readline.read_history_file(HISTORY_FILE)
except FileNotFoundError:
    pass

readline.set_history_length(1000)

def run_code(code):
    tokens = Lexer(code).tokenize()
    ast = Parser(tokens).parse()
    evaluator.set_ast(ast)

    return evaluator.eval()


def normalize_code(code: str) -> str:
    """Normalize code read from files or multi-line input:
    - Convert groups of 4 leading spaces to tabs to match REPL behavior
    - Normalize line endings to LF
    - Decode escape sequences (unicode_escape)
    """
    # Normalize CRLF to LF
    code = code.replace('\r\n', '\n').replace('\r', '\n')

    lines = code.split('\n')
    normalized_lines = []

    for line in lines:
        if not line:
            normalized_lines.append(line)
            continue

        # Count leading spaces (but prefer existing tabs)
        leading_spaces = len(line) - len(line.lstrip(' '))
        if leading_spaces > 0 and (line.lstrip(' ')[0:1] != "\t"):
            if leading_spaces % 4 != 0:
                raise RuntimeError("Indentation error: expected multiples of 4 spaces in file input")
            tabs = leading_spaces // 4
            remainder = line.lstrip(' ')
            normalized_lines.append("\t" * tabs + remainder)
        else:
            normalized_lines.append(line)

    normalized = "\n".join(normalized_lines)
    # Decode escape sequences (so file contents containing "\\n" become real newlines)
    normalized = normalized.encode().decode('unicode_escape')
    return normalized

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="Run unit tests"
    )

    parser.add_argument(
        "-f",
        "--file",
        type=str,
        help="Run a Python file instead of starting the REPL"
    )

    args = parser.parse_args()

    if args.test:
        raise SystemExit(pytest.main([str(TEST_DIR)]))
    
    if args.file:
        with open(args.file, "r") as f:
            code = f.read()
            code = normalize_code(code)
            result = run_code(code)
        return

    print("*********************** Python Interpreter, version 1.0, by Brayden Clark ***********************")
    print("****** Welcome to the Python Interpreter! Type 'exit' to quit, 'clear' to clear the screen ******")

    depth = 0

    while True:
        try:
            try:
                line = input(MAIN_PROMPT)
            except KeyboardInterrupt:
                print("KeyboardInterrupt")
                continue

            if line.strip() == "exit":
                break

            if line.strip() == "clear" or line.strip() == "clear()":
                os.system(clear_arg)
                print("*********************** Python Interpreter, version 1.0, by Brayden Clark ***********************")
                print("****** Welcome to the Python Interpreter! Type 'exit' to quit, 'clear' to clear the screen ******")
                continue

            # If the line starts a block (ends with ':'), read subsequent
            # indented lines until a blank line is entered.
            if line.rstrip().endswith(":"):
                depth += 1
                lines = [line]
                aborted = False
                while True:
                    readline.set_startup_hook(lambda d=depth: readline.insert_text("    " * d))
                    try:
                        next_line = input(CONT_PROMPT)
                    except KeyboardInterrupt:
                        print("KeyboardInterrupt")
                        aborted = True
                        break
                    finally:
                        readline.set_startup_hook(None)

                    if next_line.rstrip().endswith(":"):
                        depth += 1

                    if next_line.strip() == "":
                        depth = 0
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
                        print(repr(result))
            else:
                print(repr(result))

        except Exception as e:
            print(f"Error: {e}")