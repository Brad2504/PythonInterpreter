# Python Parser

from pyinterp.lexer import Lexer as Lexer

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
    
    def parse(self):
        # split tokens based on newlines and parse each line as an expression
        expressions = []
        lines = []
        current_line = []
        for token in self.tokens:
            if token[0] == "NEWLINE":
                if current_line:
                    lines.append(current_line)
                    current_line = []
            else:
                current_line.append(token)
        if current_line:
            lines.append(current_line)
        
        for line in lines:
            if line:
                indent = 0
                while indent < len(line) and line[indent][0] == "TAB":
                    indent += 1
                expressions.append((indent, self.parse_expr(line[indent:])))
        return expressions

    def split_on_top_level_operator(self, tokens, operators):
        pos = 0
        depth = 0

        for token in tokens:
            if token[0] == "LPAREN":
                depth += 1
            elif token[0] == "RPAREN":
                depth -= 1
            elif (token[0] in ["OP", "PLUSEQUALS", "MINUSEQUALS", "STAREQUALS", "SLASHEQUALS"]) and (token[1] in operators) and (depth == 0):
                return tokens[:pos], token[1], tokens[pos + 1:]
            pos += 1
        return None, None, None
    
    def split_inline_conditionals(self, tokens):
        pos_0 = 0
        pos_1 = 0
        
        for token in tokens:
            if token[0] == "CONDITIONAL" and token[1] == "if":
                pos_0 = tokens.index(token)
            elif token[0] == "CONDITIONAL" and token[1] == "else":
                pos_1 = tokens.index(token)
        
        if (pos_0 != 0 and pos_1 == 0) or (pos_0 == 0 and pos_1 != 0):
            raise RuntimeError("Expected 'if' and 'else' in conditional expression")
        
        true_tokens = tokens[:pos_0]
        condition_tokens = tokens[pos_0 + 1:pos_1]
        false_tokens = tokens[pos_1 + 1:]

        if not true_tokens or not condition_tokens or not false_tokens:
            return None, None, None
        
        return true_tokens, condition_tokens, false_tokens
    
    def split_multiline_conditionals(self, tokens):
        pos_cond_word = None
        condition_tokens = []
        pos_colon = 0

        for token in tokens:
            if token[0] == "CONDITIONAL" and token[1] in ["if", "elif", "else"]:
                pos_cond_word = token[1]
            elif token[0] == "COLON":
                pos_colon = tokens.index(token)
            
        if pos_cond_word == "if" or pos_cond_word == "elif":
            condition_tokens = tokens[1:pos_colon]

        if pos_cond_word is None or pos_colon == 0:
            raise RuntimeError("Expected conditional keyword and colon in conditional expression")
        
        return pos_cond_word, condition_tokens

    def split_on_last_top_level_dot(self, tokens):
        depth = 0
        last_dot = None

        for pos, token in enumerate(tokens):
            if token[0] == "LPAREN":
                depth += 1
            elif token[0] == "RPAREN":
                depth -= 1
            elif token[0] == "DOT" and depth == 0:
                last_dot = pos

        if last_dot is None:
            return None, None

        return tokens[:last_dot], tokens[last_dot + 1:]

    def parse_expr(self, tokens):
        if len(tokens) == 0:
            raise RuntimeError("Unexpected end of expression")

        if tokens[0][0] == "RPAREN":
            raise RuntimeError("Unexpected token: RPAREN")
        
        left_tokens, operator, right_tokens = self.split_on_top_level_operator(tokens, ["+=", "-=", "*=", "/="])
        if operator is not None:
            return ("binop", operator, self.parse_expr(left_tokens), self.parse_expr(right_tokens))

        if tokens[0][0] == "IDENT" and len(tokens) > 1 and tokens[1][0] == "ASSIGN":
            return ("assign", tokens[0][1], self.parse_expr(tokens[2:]))
        
        # if tokens[0][0] == "PRINT":
        #     pos = 1
        #     text_tokens = []
        #     while pos < len(tokens) and tokens[pos][0] != "RPAREN":
        #         text_tokens.append(tokens[pos])
        #         pos += 1
        #     if pos >= len(tokens) or tokens[pos][0] != "RPAREN":
        #         raise RuntimeError("Expected closing parenthesis in print statement")

        #     return ("print", self.parse_expr(text_tokens))

        if tokens[0][0] == "IMPORT":
            if len(tokens) < 2:
                raise RuntimeError("Expected module name after 'import'")

            module_parts = []
            as_name = None
            pos = 1
            while pos < len(tokens):
                if tokens[pos][0] == "AS":
                    if pos + 1 >= len(tokens) or tokens[pos + 1][0] != "IDENT":
                        raise RuntimeError("Expected alias name after 'as' in import statement")
                    as_name = tokens[pos + 1][1]
                    break
                if tokens[pos][0] == "IDENT":
                    module_parts.append(tokens[pos][1])
                elif tokens[pos][0] == "DOT":
                    module_parts.append(".")
                else:
                    raise RuntimeError("Expected module name after 'import'")
                pos += 1

            module_name = "".join(module_parts)
            if as_name:
                return ("import", module_name, as_name)
            return ("import", module_name)
        
        if tokens[0][0] == "FROM":
            if len(tokens) < 4:
                raise RuntimeError("Expected syntax: from <module> import <name>")
            
            module_parts = []
            pos = 1
            while pos < len(tokens) and tokens[pos][0] != "IMPORT":
                if tokens[pos][0] == "IDENT":
                    module_parts.append(tokens[pos][1])
                elif tokens[pos][0] == "DOT":
                    module_parts.append(".")
                else:
                    raise RuntimeError("Expected syntax: from <module> import <name>")
                pos += 1

            if pos >= len(tokens) or tokens[pos][0] != "IMPORT":
                raise RuntimeError("Expected syntax: from <module> import <name>")

            module_name = "".join(module_parts)

            if pos + 1 >= len(tokens) or tokens[pos + 1][0] != "IDENT":
                raise RuntimeError("Expected syntax: from <module> import <name>")

            name = tokens[pos + 1][1]

            if pos + 2 < len(tokens) and tokens[pos + 2][0] == "AS":
                if pos + 3 >= len(tokens) or tokens[pos + 3][0] != "IDENT":
                    raise RuntimeError("Expected alias name after 'as' in from-import statement")
                as_name = tokens[pos + 3][1]
                return ("from_import", module_name, name, as_name)

            return ("from_import", module_name, name)

        if tokens[0][0] == "FOR":
            if tokens[1][0] != "IDENT" or tokens[2][0] != "IN":
                raise RuntimeError("Expected syntax: for <var> in <iterable>")
            var_name = tokens[1][1]
            iterable_tokens = tokens[3:]
            return ("for", var_name, self.parse_expr(iterable_tokens))
        
        if tokens[0][0] == "WHILE":
            condition_tokens = tokens[1:]
            return ("while", self.parse_expr(condition_tokens))

        if len(tokens) > 3 and tokens[0][0] == "IDENT" and tokens[1][0] == "DOT" and tokens[2][0] == "IDENT" and tokens[3][0] == "ASSIGN":
            obj_name = tokens[0][1]
            attr_name = tokens[2][1]
            value_tokens = tokens[4:]
            return ("set_attr", obj_name, attr_name, self.parse_expr(value_tokens))

        if tokens[0][0] == "DEF" and len(tokens) > 1 and tokens[1][0] == "FUNCTION":
            func_name = tokens[1][1]
            if len(tokens) < 4 or tokens[2][0] != "LPAREN":
                raise RuntimeError("Expected function name followed by parentheses in function definition")
            
            params = []
            pos = 3
            while pos < len(tokens) and tokens[pos][0] != "RPAREN":
                if tokens[pos][0] == "IDENT":
                    params.append(tokens[pos][1])
                elif tokens[pos][0] == "COMMA":
                    pass  # Ignore commas between parameters
                else:
                    raise RuntimeError("Unexpected token in function parameters")
                pos += 1
            
            if pos >= len(tokens) or tokens[pos][0] != "RPAREN":
                raise RuntimeError("Expected closing parenthesis in function definition")
            
            return ("def", func_name, params)

        if tokens[0][0] == "CONDITIONAL":
            pos_cond_word, condition_tokens = self.split_multiline_conditionals(tokens)
            if condition_tokens:
                return (pos_cond_word, self.parse_expr(condition_tokens))
            else:
                return (pos_cond_word, None)
            
        if tokens[0][0] == "RETURN":
            if len(tokens) == 1:
                return ("return", None)
            return ("return", self.parse_expr(tokens[1:]))

        if tokens[0][0] == "CLASS":
            if len(tokens) < 2 or tokens[1][0] != "IDENT":
                raise RuntimeError("Expected class name after 'class'")

            class_name = tokens[1][1]
            return ("class_def", class_name)

        true_tokens, condition_tokens, false_tokens = self.split_inline_conditionals(tokens)
        if true_tokens is not None:
            return ("inlinecond", self.parse_expr(condition_tokens), self.parse_expr(true_tokens), self.parse_expr(false_tokens))

        left_tokens, operator, right_tokens = self.split_on_top_level_operator(tokens, ["and", "or"])
        if operator is not None:
            return ("binop", operator, self.parse_expr(left_tokens), self.parse_expr(right_tokens))

        left_tokens, operator, right_tokens = self.split_on_top_level_operator(tokens, ["<", ">", "<=", ">=", "==", "!="])
        if operator is not None:
            return ("binop", operator, self.parse_expr(left_tokens), self.parse_expr(right_tokens))
        
        left_tokens, operator, right_tokens = self.split_on_top_level_operator(tokens, ["+", "-"])
        if operator is not None:
            return ("binop", operator, self.parse_expr(left_tokens), self.parse_expr(right_tokens))

        left_tokens, operator, right_tokens = self.split_on_top_level_operator(tokens, ["*", "/"])
        if operator is not None:   
            return ("binop", operator, self.parse_expr(left_tokens), self.parse_expr(right_tokens))

        left_tokens, right_tokens = self.split_on_last_top_level_dot(tokens)
        if left_tokens is not None:
            left_expr = self.parse_expr(left_tokens)

            if not right_tokens:
                raise RuntimeError("Expected attribute name after '.'")

            if right_tokens[0][0] not in ("IDENT", "FUNCTION"):
                raise RuntimeError("Expected attribute name after '.'")

            attr_name = right_tokens[0][1]

            if len(right_tokens) > 1 and right_tokens[1][0] == "LPAREN":
                args = []
                pos = 2
                arg_start = pos
                depth = 0

                while pos < len(right_tokens):
                    tk = right_tokens[pos]
                    if tk[0] == "LPAREN":
                        depth += 1
                    elif tk[0] == "RPAREN":
                        if depth == 0:
                            if pos > arg_start:
                                args.append(self.parse_expr(right_tokens[arg_start:pos]))
                            break
                        depth -= 1
                    elif tk[0] == "COMMA" and depth == 0:
                        if pos > arg_start:
                            args.append(self.parse_expr(right_tokens[arg_start:pos]))
                        arg_start = pos + 1
                    pos += 1

                if pos >= len(right_tokens) or right_tokens[pos][0] != "RPAREN":
                    raise RuntimeError("Expected closing parenthesis in attribute call")

                return ("attr_call", left_expr, attr_name, args)

            if len(right_tokens) == 1:
                return ("get_attr", left_expr, attr_name)

            raise RuntimeError("Unexpected token sequence after attribute access")

        if tokens[0][0] in ("IDENT", "FUNCTION") and len(tokens) > 1 and tokens[1][0] == "LPAREN":
            func_name = tokens[0][1]
            args = []
            pos = 2

            # Collect tokens for each argument, splitting on top-level commas
            arg_start = pos
            depth = 0
            while pos < len(tokens):
                tk = tokens[pos]
                if tk[0] == "LPAREN":
                    depth += 1
                elif tk[0] == "RPAREN":
                    if depth == 0:
                        # end of arg list
                        if pos > arg_start:
                            args.append(self.parse_expr(tokens[arg_start:pos]))
                        break
                    depth -= 1
                elif tk[0] == "COMMA" and depth == 0:
                    if pos > arg_start:
                        args.append(self.parse_expr(tokens[arg_start:pos]))
                    arg_start = pos + 1
                pos += 1

            if pos >= len(tokens) or tokens[pos][0] != "RPAREN":
                raise RuntimeError("Expected closing parenthesis in function call")

            return ("call", ("ident", func_name), args)

        if tokens[0][0] == "LPAREN":
            return self.parse_paran(tokens)
        
        if tokens[0][0] == "IDENT":
            return ("ident", tokens[0][1])

        if tokens[0][0] == "NUMBER":
            return ("number", tokens[0][1])

        if tokens[0][0] == "BOOLEAN":
            return ("boolean", tokens[0][1] == "True")
        
        if tokens[0][0] in ("DOUBLEQUOTE", "SINGLEQUOTE"):
            return ("string", tokens[0][1][1:-1]) 
        
        if tokens[0][0] == "LIST":
            raw = tokens[0][1]
            content = raw[1:-1].strip()
            if not content:
                return ("list", [])
            item_tokens = []
            depth = 0
            current_item = []
            for char in content:
                if char == ',' and depth == 0:
                    item_tokens.append(current_item)
                    current_item = []
                else:
                    if char == '(':
                        depth += 1
                    elif char == ')':
                        depth -= 1
                    current_item.append(char)
            if current_item:
                item_tokens.append(current_item)
            
            items = []
            for item in item_tokens:
                item_str = ''.join(item).strip()
                if item_str:
                    tokens = Lexer(item_str).tokenize()
                    items.append(self.parse_expr(tokens))
            return ("list", items)

        if tokens[0][0] in ("FSTRING_DQ", "FSTRING_SQ"):
            raw = tokens[0][1]
            content = raw[2:-1]
            parts = []
            i = 0
            while i < len(content):
                if content[i] == '{':
                    expr_start = i + 1
                    
                    while i < len(content) and content[i] != '}':
                        i += 1

                    if i == len(content):
                        raise RuntimeError("Unmatched '{' in f-string")
                    
                    expr_tokens = Lexer(content[expr_start:i]).tokenize()
                    expr_ast = self.parse_expr(expr_tokens)
                    parts.append(('expr', expr_ast))

                    i = i + 1
                else:
                    j = i
                    while j < len(content) and content[j] != '{':
                        j += 1
                    parts.append(('string', content[i:j]))
                    i = j

            return ("fstring", parts)

        raise RuntimeError(f"Unexpected token: {tokens[0]}")

    def parse_paran(self, tokens):
        pos = 1
        depth = 1
        left_tokens = []

        while pos < len(tokens):
            if tokens[pos][0] == "LPAREN":
                depth += 1
            elif tokens[pos][0] == "RPAREN":
                depth -= 1
            
            if depth == 0:
                break

            left_tokens.append(tokens[pos])
            pos += 1
        
        if depth != 0:
            raise RuntimeError("Unmatched parenthesis")

        if pos + 1 < len(tokens) and tokens[pos + 1][0] == "OP":
            operator = tokens[pos + 1][1]
            right_tokens = tokens[pos + 2:]
            return ("binop", operator, self.parse_expr(left_tokens), self.parse_expr(right_tokens))
        else:
            return self.parse_expr(left_tokens)

    def parse_comparison(self, tokens):
        pos = 0
        left_tokens = []

        while pos < len(tokens) and not (tokens[pos][0] == "OP" and tokens[pos][1] in ["<", ">", "<=", ">=", "==", "!="]):
            left_tokens.append(tokens[pos])
            pos += 1

        if pos >= len(tokens):
            raise RuntimeError("Expected operator")

        operator = tokens[pos][1]
        right_tokens = tokens[pos + 1:]
        return ("binop", operator, self.parse_expr(left_tokens), self.parse_expr(right_tokens))
    
    def parse_binop(self, tokens):
        pos = 0
        left_tokens = []
        right_tokens = []
        
        while pos < len(tokens) and not (tokens[pos][0] == "OP" and tokens[pos][1] in ["+", "-"]):
            left_tokens.append(tokens[pos])
            pos += 1
        
        if len(left_tokens) == len(tokens):
            pos = 0
            left_tokens = []
            while pos < len(tokens) and not (tokens[pos][0] == "OP" and tokens[pos][1] in ["*", "/"]):
                left_tokens.append(tokens[pos])
                pos += 1
            
            if len(left_tokens) == len(tokens):
                raise RuntimeError("Expected operator")
        
        if pos >= len(tokens):
            raise RuntimeError("Expected operator")

        operator = tokens[pos][1]
        right_tokens = tokens[pos+1:]
        return ("binop", operator, self.parse_expr(left_tokens), self.parse_expr(right_tokens))