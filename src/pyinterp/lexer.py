# Python Lexer

import re

class Lexer:
    def __init__(self, code):
        self.code = code
        self.tokens = []
    
    def tokenize_format_spec(self):
        token_specification = [
            ('NUMBER',   r'\d+'),
            ('DOT',      r'\.'),
            ('LBRACKET', r'\['),
            ('RBRACKET', r'\]'),
            ('LBRACE',   r'\{'),
            ('RBRACE',   r'\}'),
            ('LPAREN',   r'\('),
            ('RPAREN',   r'\)'),
            ('PLUSEQUALS', r'\+='),
            ('MINUSEQUALS', r'-='),
            ('STAREQUALS', r'\*='),
            ('PERCENTEQUALS', r'%='),
            ('FLOORDIVEQUALS', r'//='),
            ('SLASHEQUALS', r'/='),
            ('OP', r'\*\*|//|==|!=|<=|>=|:=|[+\-*/%<>]=?|and|or|not'),
            ('COLON',    r':'),
            ('BOOLEAN',   r'\bTrue\b|\bFalse\b'),
            ('PI',       r'\bpi\b|\bPI\b'),
            ('FOR',      r'\bfor\b'),
            ('IN',       r'\bin\b'),
            ('WHILE',    r'\bwhile\b'),
            ('IMPORT',   r'\bimport\b'),
            ('FROM',     r'\bfrom\b'),
            ('AS',       r'\bas\b'),
            ('RETURN',   r'\breturn\b'),
            ('FUNCTION', r'[A-Za-z_]\w*(?=\()'),
            ('DEF',      r'\bdef\b'),
            ('COMMA',    r','),
            ('DOUBLEQUOTE',    r'"(?:\\.|[^"\\])*"'),
            ('SINGLEQUOTE',    r"'(?:\\.|[^'\\])*'"),
            ('IDENT',    r'[A-Za-z_]\w*'),
            ('SKIP',     r'[ \t]+'),
            ('MISMATCH', r'.'),
        ]

        tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
        tokens = []

        for mo in re.finditer(tok_regex, self.code):
            kind = mo.lastgroup
            value = mo.group()

            if kind == 'SKIP':
                continue
            if kind == 'MISMATCH':
                raise RuntimeError(f'Unexpected character in format specification: {value}')
            if kind in ('NUMBER',):
                value = int(value)

            tokens.append((kind, value))

        return tokens

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
            ('PERCENTEQUALS', r'%='),         # %= operator
            ('FLOORDIVEQUALS', r'//='),      # //= operator
            ('SLASHEQUALS', r'/='),           # /= operator
            ('OP',       r'\*\*|//|==|!=|<=|>=|:=|[+\-*/%<>]=?|and|or|not'),  # Operators
            ('COLON',    r':'),              # Colon
            ('CONDITIONAL', r'\bif\b|\belse\b|\belif\b'),     # Conditional keywords
            ('ASSIGN',   r'='),              # Assignment operator
            ('CLASS',    r'\bclass\b'),          # Class definition keyword
            ('PI',       r'\bpi\b|\bPI\b'),                # pi constant
            ('FOR',      r'\bfor\b'),            # For loop keyword
            ('IN',       r'\bin\b'),             # In keyword for loops
            ('WHILE',    r'\bwhile\b'),          # While loop keyword
            ('IMPORT',   r'\bimport\b'),         # import keyword
            ('FROM',     r'\bfrom\b'),           # from keyword
            ('AS',       r'\bas\b'),             # as keyword for imports
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
            elif kind in ('OP', 'LPAREN', 'RPAREN', 'NEWLINE', 'IDENT', 'CONDITIONAL', 'COMMENT', 'COLON', 'TAB', 'ASSIGN', 'FUNCTION', 'DEF', 'RETURN', 'COMMA', 'PRINT', 'DOUBLEQUOTE', 'SINGLEQUOTE', 'PLUSEQUALS', 'MINUSEQUALS', 'STAREQUALS', 'PERCENTEQUALS', 'FLOORDIVEQUALS', 'SLASHEQUALS', 'BOOLEAN', 'DOT', 'AS', 'CLASS', 'PI', 'FOR', 'IN', 'WHILE', 'IMPORT', 'FROM'):
                pass  # Keep as string
            self.tokens.append((kind, value))
        return self.tokens