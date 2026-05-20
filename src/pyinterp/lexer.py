# Python Lexer

import re

class Lexer:
    def __init__(self, code):
        self.code = code
        self.tokens = []

    def tokenize(self):
        token_specification = [
            ('NUMBER',   r'\d+(\.\d*)?'),    # Integer or decimal number
            ('LIST',     r'\[.*?\]'),         # List literals (non-greedy match)
            ('LPAREN',   r'\('),             # Left parenthesis
            ('RPAREN',   r'\)'),             # Right parenthesis
            ('PLUSEQUALS', r'\+='),            # += operator
            ('MINUSEQUALS', r'-='),           # -= operator
            ('STAREQUALS', r'\*='),           # *= operator
            ('SLASHEQUALS', r'/='),           # /= operator
            ('OP',       r'==|!=|<=|>=|[+\-*/<>]|and|or'),  # Operators
            ('COLON',    r':'),              # Colon
            ('CONDITIONAL', r'if|else|elif'),     # Conditional keywords
            ('ASSIGN',   r'='),              # Assignment operator
            # ('PRINT',    r'print\('),        # Print token includes opening parenthesis
            ('FOR'     , r'for'),            # For loop keyword
            ('IN'      , r'in'),             # In keyword for loops
            ('WHILE'   , r'while'),          # While loop keyword
            ('RETURN',   r'return'),         # Return statement keyword
            ('FUNCTION', r'[A-Za-z_]\w*(?=\()'),  # Function names (identifiers followed by a parenthesis)
            ('DEF',      r'def'),            # Function definition keyword
            ('COMMA',    r','),              # Comma
            ('FSTRING_DQ', r'f"(?:\\.|[^"\\])*"'),  # f"..."
            ('FSTRING_SQ', r"f'(?:\\.|[^'\\])*'"),    # f'...'
            ('BOOLEAN',   r'\bTrue\b|\bFalse\b'),  # Boolean literals
            ('IDENT',    r'[A-Za-z_]\w*'),   # Identifiers
            ('DOUBLEQUOTE',    r'"(?:\\.|[^"\\])*"'),  # Double-quoted string
            ('SINGLEQUOTE',    r"'(?:\\.|[^'\\])*'"),  # Single-quoted string
            ('NEWLINE',  r'\n'),             # Line endings
            ('TAB',      r'\t'),             # Tabs
            ('SKIP',     r'[ \t]+'),         # Skip over spaces and tabs
            ('COMMENT',  r'#.*'),            # Comments
            ('MISMATCH', r'.'),              # Any other character
        ]
        tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
        for mo in re.finditer(tok_regex, self.code):
            kind = mo.lastgroup
            value = mo.group()
            if kind == 'NUMBER':
                value = float(value) if '.' in value else int(value)
            elif kind == 'SKIP':
                continue  # Ignore whitespace
            elif kind == 'MISMATCH':
                raise RuntimeError(f'Unexpected character: {value}')
            elif kind in ('OP', 'LPAREN', 'RPAREN', 'NEWLINE', 'IDENT', 'CONDITIONAL', 'COMMENT', 'COLON', 'TAB', 'ASSIGN', 'FUNCTION', 'DEF', 'RETURN', 'COMMA', 'PRINT', 'DOUBLEQUOTE', 'SINGLEQUOTE', 'PLUSEQUALS', 'MINUSEQUALS', 'STAREQUALS', 'SLASHEQUALS', 'BOOLEAN'):
                pass  # Keep as string
            self.tokens.append((kind, value))
        return self.tokens