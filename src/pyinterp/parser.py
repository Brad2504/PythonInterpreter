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

    def parse_stmt(self, tokens):
        return self.parse_expr(tokens)

    def parse_primary(self, tokens):
        if not tokens:
            raise RuntimeError("Unexpected end of expression")

        token_type = tokens[0][0]

        if token_type in ("IDENT", "FUNCTION"):
            return ("ident", tokens[0][1])
        if token_type == "NUMBER":
            return ("number", tokens[0][1])
        if token_type == "BOOLEAN":
            return ("boolean", tokens[0][1] == "True")
        if token_type in ("DOUBLEQUOTE", "SINGLEQUOTE"):
            return ("string", tokens[0][1][1:-1])
        if token_type == "LPAREN":
            close_pos = self.find_matching(tokens, 0, "LPAREN", "RPAREN")
            tokens_inside = tokens[1:close_pos]

            tuple_elements = self.split_top_level_items(tokens_inside)
            if len(tuple_elements) > 1:
                return ("tuple", [self.parse_expr(elem) for elem in tuple_elements])
            else:
                return self.parse_paran(tokens)
        if token_type == "LBRACKET":
            return self.parse_list(tokens)
        if token_type == "LBRACE":
            return self.parse_dict(tokens)
        if token_type in ("FSTRING_DQ", "FSTRING_SQ"):
            raw = tokens[0][1]
            content = raw[2:-1]
            parts = []
            i = 0

            while i < len(content):
                if content[i] == "{":
                    expr_start = i + 1
                    brace_depth = 1
                    i += 1

                    while i < len(content) and brace_depth > 0:
                        if content[i] == "{":
                            brace_depth += 1
                        elif content[i] == "}":
                            brace_depth -= 1
                        i += 1

                    if brace_depth != 0:
                        raise RuntimeError("Unmatched '{' in f-string")

                    expr_tokens = Lexer(content[expr_start:i - 1]).tokenize()
                    parts.append(("expr", self.parse_expr(expr_tokens)))
                else:
                    j = i
                    while j < len(content) and content[j] != "{":
                        j += 1
                    parts.append(("string", content[i:j]))
                    i = j

            return ("fstring", parts)

        raise RuntimeError(f"Unexpected token in primary: {tokens[0]}")

    def find_matching(self, tokens, start_pos, open_type, close_type):
        depth = 0
        for pos in range(start_pos, len(tokens)):
            if tokens[pos][0] == open_type:
                depth += 1
            elif tokens[pos][0] == close_type:
                depth -= 1
                if depth == 0:
                    return pos
        raise RuntimeError(f"Expected matching {close_type} for {open_type}")

    def find_top_level_index(self, tokens, token_types):
        paren_depth = 0
        bracket_depth = 0
        brace_depth = 0

        for pos, token in enumerate(tokens):
            if token[0] == "LPAREN":
                paren_depth += 1
            elif token[0] == "RPAREN":
                paren_depth -= 1
            elif token[0] == "LBRACKET":
                bracket_depth += 1
            elif token[0] == "RBRACKET":
                bracket_depth -= 1
            elif token[0] == "LBRACE":
                brace_depth += 1
            elif token[0] == "RBRACE":
                brace_depth -= 1
            elif token[0] in token_types and paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
                return pos

        return None

    def parse_unpack_target(self, tokens):
        if not tokens:
            raise RuntimeError("Expected unpack target")

        if tokens[0][0] == "LPAREN":
            close_pos = self.find_matching(tokens, 0, "LPAREN", "RPAREN")
            if close_pos == len(tokens) - 1:
                tokens = tokens[1:close_pos]
            
        if tokens[0][0] == "LBRACKET":
            close_pos = self.find_matching(tokens, 0, "LBRACKET", "RBRACKET")
            if close_pos == len(tokens) - 1:
                tokens = tokens[1:close_pos]
        
        if tokens[0][0] == "LBRACE":
            raise RuntimeError("Cannot assign to a dictionary literal")

        parts = self.split_top_level_items(tokens)

        if len(parts) == 1:
            part = parts[0]
            if len(part) == 1 and part[0][0] == "IDENT":
                return ("ident", part[0][1])
            return self.parse_unpack_target(part)

        return ("tuple", [self.parse_unpack_target(part) for part in parts])

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

    def parse_expr(self, tokens):
        if len(tokens) == 0:
            raise RuntimeError("Unexpected end of expression")

        if tokens[0][0] == "RPAREN":
            raise RuntimeError("Unexpected token: RPAREN")
        
        left_tokens, operator, right_tokens = self.split_on_top_level_operator(tokens, ["+=", "-=", "*=", "/="])
        if operator is not None:
            return ("binop", operator, self.parse_expr(left_tokens), self.parse_expr(right_tokens))

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
            in_pos = self.find_top_level_index(tokens, {"IN"})
            if in_pos is None or in_pos < 2:
                raise RuntimeError("Expected syntax: for <var> in <iterable>")
            target_tokens = tokens[1:in_pos]
            iterable_tokens = tokens[in_pos + 1:]
            if iterable_tokens and iterable_tokens[-1][0] == "COLON":
                iterable_tokens = iterable_tokens[:-1]
            if not target_tokens or not iterable_tokens:
                raise RuntimeError("Expected iterable expression in for statement")
            return ("for", self.parse_unpack_target(target_tokens), self.parse_expr(iterable_tokens))

        if tokens[0][0] == "WHILE":
            condition_tokens = tokens[1:]
            if condition_tokens and condition_tokens[-1][0] == "COLON":
                condition_tokens = condition_tokens[:-1]
            if not condition_tokens:
                raise RuntimeError("Expected condition expression in while statement")
            return ("while", self.parse_expr(condition_tokens))

        if len(tokens) > 3 and tokens[0][0] == "IDENT" and tokens[1][0] == "DOT" and tokens[2][0] == "IDENT" and tokens[3][0] == "ASSIGN":
            obj_name = tokens[0][1]
            attr_name = tokens[2][1]
            value_tokens = tokens[4:]
            return ("set_attr", ("ident", obj_name), attr_name, self.parse_expr(value_tokens))

        assign_pos = self.find_top_level_index(tokens, {"ASSIGN"})
        if assign_pos is not None:
            target_tokens = tokens[:assign_pos]
            value_tokens = tokens[assign_pos + 1:]
            if not target_tokens or not value_tokens:
                raise RuntimeError("Expected syntax: <target> = <value>")
            return ("assign", self.parse_unpack_target(target_tokens), self.parse_expr(value_tokens))

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

        postfix_expr = self.parse_postfix(tokens)
        if postfix_expr is not None:
            return postfix_expr

        if tokens[0][0] == "LBRACE":
            return self.parse_dict(tokens)

        if tokens[0][0] == "LPAREN":
            return self.parse_paran(tokens)

        return self.parse_primary(tokens)
    
    def parse_list(self, tokens):
        if not tokens or tokens[0][0] != "LBRACKET":
            raise RuntimeError("Expected list literal")

        close_pos = self.find_matching(tokens, 0, "LBRACKET", "RBRACKET")
        content_tokens = tokens[1:close_pos]

        elements = []
        start = 0
        paren_depth = 0
        bracket_depth = 0
        brace_depth = 0

        for pos, token in enumerate(content_tokens):
            if token[0] == "LPAREN":
                paren_depth += 1
            elif token[0] == "RPAREN":
                paren_depth -= 1
            elif token[0] == "LBRACKET":
                bracket_depth += 1
            elif token[0] == "RBRACKET":
                bracket_depth -= 1
            elif token[0] == "LBRACE":
                brace_depth += 1
            elif token[0] == "RBRACE":
                brace_depth -= 1
            elif token[0] == "COMMA" and paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
                if pos > start:
                    elements.append(self.parse_expr(content_tokens[start:pos]))
                start = pos + 1

        if start < len(content_tokens):
            elements.append(self.parse_expr(content_tokens[start:]))

        return ("list", elements)

    def split_top_level_items(self, item_tokens):
            items = []
            start = 0
            paren_depth = 0
            bracket_depth = 0
            brace_depth = 0

            for pos, token in enumerate(item_tokens):
                if token[0] == "LPAREN":
                    paren_depth += 1
                elif token[0] == "RPAREN":
                    paren_depth -= 1
                elif token[0] == "LBRACKET":
                    bracket_depth += 1
                elif token[0] == "RBRACKET":
                    bracket_depth -= 1
                elif token[0] == "LBRACE":
                    brace_depth += 1
                elif token[0] == "RBRACE":
                    brace_depth -= 1
                elif token[0] == "COMMA" and paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
                    if pos > start:
                        items.append(item_tokens[start:pos])
                    start = pos + 1

            if start < len(item_tokens):
                items.append(item_tokens[start:])

            return [item for item in items if item]

    def parse_dict(self, tokens):
        if not tokens or tokens[0][0] != "LBRACE":
            raise RuntimeError("Expected dictionary literal")

        close_pos = self.find_matching(tokens, 0, "LBRACE", "RBRACE")
        content_tokens = tokens[1:close_pos]

        pairs = []
        start = 0
        paren_depth = 0
        bracket_depth = 0
        brace_depth = 0

        def add_pair(pair_tokens):
            colon_pos = None
            nested_paren = 0
            nested_bracket = 0
            nested_brace = 0

            for i, token in enumerate(pair_tokens):
                if token[0] == "LPAREN":
                    nested_paren += 1
                elif token[0] == "RPAREN":
                    nested_paren -= 1
                elif token[0] == "LBRACKET":
                    nested_bracket += 1
                elif token[0] == "RBRACKET":
                    nested_bracket -= 1
                elif token[0] == "LBRACE":
                    nested_brace += 1
                elif token[0] == "RBRACE":
                    nested_brace -= 1
                elif token[0] == "COLON" and nested_paren == 0 and nested_bracket == 0 and nested_brace == 0:
                    colon_pos = i
                    break

            if colon_pos is None:
                raise RuntimeError("Expected ':' in dictionary pair")

            key_tokens = pair_tokens[:colon_pos]
            value_tokens = pair_tokens[colon_pos + 1:]
            pairs.append((self.parse_expr(key_tokens), self.parse_expr(value_tokens)))

        for pos, token in enumerate(content_tokens):
            if token[0] == "LPAREN":
                paren_depth += 1
            elif token[0] == "RPAREN":
                paren_depth -= 1
            elif token[0] == "LBRACKET":
                bracket_depth += 1
            elif token[0] == "RBRACKET":
                bracket_depth -= 1
            elif token[0] == "LBRACE":
                brace_depth += 1
            elif token[0] == "RBRACE":
                brace_depth -= 1
            elif token[0] == "COMMA" and paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
                if pos > start:
                    add_pair(content_tokens[start:pos])
                start = pos + 1

        if start < len(content_tokens):
            add_pair(content_tokens[start:])

        return ("dict", pairs)
    
    def parse_postfix(self, tokens):
        if not tokens:
            return None

        token_type = tokens[0][0]
        if token_type not in ("IDENT", "FUNCTION", "NUMBER", "BOOLEAN", "DOUBLEQUOTE", "SINGLEQUOTE", "LPAREN", "LBRACKET", "LBRACE", "FSTRING_DQ", "FSTRING_SQ"):
            return None

        if token_type in ("IDENT", "FUNCTION", "NUMBER", "BOOLEAN", "DOUBLEQUOTE", "SINGLEQUOTE", "FSTRING_DQ", "FSTRING_SQ"):
            primary_end = 1
        elif token_type == "LPAREN":
            primary_end = self.find_matching(tokens, 0, "LPAREN", "RPAREN") + 1
        elif token_type == "LBRACKET":
            primary_end = self.find_matching(tokens, 0, "LBRACKET", "RBRACKET") + 1
        else:
            primary_end = self.find_matching(tokens, 0, "LBRACE", "RBRACE") + 1

        expr = self.parse_primary(tokens[:primary_end])
        remaining_tokens = tokens[primary_end:]

        while remaining_tokens:
            token = remaining_tokens[0]

            if token[0] == "DOT":
                if len(remaining_tokens) < 2 or remaining_tokens[1][0] not in ("IDENT", "FUNCTION"):
                    raise RuntimeError("Expected identifier after '.'")
                
                name = remaining_tokens[1][1]
                
                if len(remaining_tokens) > 2 and remaining_tokens[2][0] == "LPAREN":
                    args_end = self.find_matching(remaining_tokens, 2, "LPAREN", "RPAREN")
                    arg_tokens = remaining_tokens[3:args_end]
                    args = [self.parse_expr(arg) for arg in self.split_top_level_items(arg_tokens)]
                    expr = ("attr_call", expr, name, args)
                    remaining_tokens = remaining_tokens[args_end + 1:]
                else:
                    expr = ("get_attr", expr, name)
                    remaining_tokens = remaining_tokens[2:]
            
            elif token[0] == "LBRACKET":
                index_end = self.find_matching(remaining_tokens, 0, "LBRACKET", "RBRACKET")
                index_tokens = remaining_tokens[1:index_end]
                index_expr = self.parse_expr(index_tokens)
                expr = ("index", expr, index_expr)
                remaining_tokens = remaining_tokens[index_end + 1:]
            
            elif token[0] == "LPAREN":
                args_end = self.find_matching(remaining_tokens, 0, "LPAREN", "RPAREN")
                arg_tokens = remaining_tokens[1:args_end]
                args = [self.parse_expr(arg) for arg in self.split_top_level_items(arg_tokens)]
                expr = ("call", expr, args)
                remaining_tokens = remaining_tokens[args_end + 1:]

        return expr

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