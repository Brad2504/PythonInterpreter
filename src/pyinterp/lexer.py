# Python Lexer

import re

class Lexer:
    def __init__(self, code):
        self.code = code
        self.tokens = []

    def tokenize(self):
        token_specification = [
            ('NUMBER',   r'\d+(\.\d*)?'),    # Integer or decimal number
            ('DOT',      r'\.'),             # Dot operator for attribute access
            ('LBRACKET', r'\['),             # Left bracket for list literals
            ('RBRACKET', r'\]'),
            ('LBRACE',   r'\{'),             # Left brace for dict literals
            ('RBRACE',   r'\}'),             # Right brace for dict literals')
            ('LPAREN',   r'\('),             # Left parenthesis
            ('RPAREN',   r'\)'),             # Right parenthesis
            ('PLUSEQUALS', r'\+='),            # += operator
            ('MINUSEQUALS', r'-='),           # -= operator
            ('STAREQUALS', r'\*='),           # *= operator
            ('SLASHEQUALS', r'/='),           # /= operator
            ('OP',       r'==|!=|<=|>=|[+\-*/<>]|and|or'),  # Operators
            ('COLON',    r':'),              # Colon
            ('CONDITIONAL', r'\bif\b|\belse\b|\belif\b'),     # Conditional keywords
            ('ASSIGN',   r'='),              # Assignment operator
            ('CLASS',    r'\bclass\b'),          # Class definition keyword
            ('FOR'     , r'\bfor\b'),            # For loop keyword
            ('IN'      , r'\bin\b'),             # In keyword for loops
            ('WHILE'   , r'\bwhile\b'),          # While loop keyword
            ('IMPORT',  r'\bimport\b'),         # import keyword
            ('FROM',    r'\bfrom\b'),           # from keyword
            ('AS',      r'\bas\b'),             # as keyword for imports
            ('RETURN',   r'\breturn\b'),         # Return statement keyword
            ('FUNCTION', r'[A-Za-z_]\w*(?=\()'),  # Function names (identifiers followed by a parenthesis)
            ('DEF',      r'\bdef\b'),            # Function definition keyword
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
            elif kind in ('OP', 'LPAREN', 'RPAREN', 'NEWLINE', 'IDENT', 'CONDITIONAL', 'COMMENT', 'COLON', 'TAB', 'ASSIGN', 'FUNCTION', 'DEF', 'RETURN', 'COMMA', 'PRINT', 'DOUBLEQUOTE', 'SINGLEQUOTE', 'PLUSEQUALS', 'MINUSEQUALS', 'STAREQUALS', 'SLASHEQUALS', 'BOOLEAN', 'DOT', 'AS'):
                pass  # Keep as string
            self.tokens.append((kind, value))
        return self.tokens