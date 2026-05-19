# Python Evaluator

import platform
import os

current_os = platform.system()

clear_arg = "cls" if current_os == "Windows" else "clear"

class Return(Exception):
    def __init__(self, value):
        self.value = value

class Evaluator:
    def __init__(self, ast):
        if ast and isinstance(ast[0], tuple) and len(ast[0]) == 2 and isinstance(ast[0][0], int):
            self.expressions = ast
        else:
            self.expressions = [(0, expr) for expr in ast]
        
        self.environment = {"exit": exit, "print": print, "int": int, "float": float, "str": str, "len": len, "range": range, "clear": lambda: os.system(clear_arg)}

    def set_ast(self, ast):
        if ast and isinstance(ast[0], tuple) and len(ast[0]) == 2 and isinstance(ast[0][0], int):
            self.expressions = ast
        else:
            self.expressions = [(0, expr) for expr in ast]
    
    def eval(self):
        self.validate_indentation()
        try:
            results, _ = self.eval_range(0, len(self.expressions))
        except Return:
            raise RuntimeError("Return outside function")

        if len(results) == 1:
            return results[0]

        return results

    def validate_indentation(self):
        self.validate_block(0, len(self.expressions), 0)

    def validate_block(self, start, end, expected_indent):
        index = start

        while index < end:
            indent, expr = self.expressions[index]

            if indent < expected_indent:
                return index

            if indent > expected_indent:
                raise RuntimeError("Indentation error: unexpected indent")

            if expr[0] == "if":
                index = self.validate_if_chain(index, end, expected_indent)
            elif expr[0] == "def":
                index = self.validate_function_definition(index, end, expected_indent)
            elif expr[0] == "while":
                index = self.validate_while_loop(index, end, expected_indent)
            elif expr[0] == "for":
                index = self.validate_for_loop(index, end, expected_indent)
            elif expr[0] in ("elif", "else"):
                raise RuntimeError("Indentation error: unexpected conditional branch")
            else:
                index += 1

        return index
    
    def validate_for_loop(self, start, end, expected_indent):
        index = start

        indent, expr = self.expressions[index]

        if indent != expected_indent or expr[0] != "for":
            raise RuntimeError("Indentation error: expected for loop")
        
        body_start = index + 1

        index = self.validate_block(body_start, end, expected_indent + 1)

        return index

    def validate_while_loop(self, start, end, expected_indent):
        index = start

        indent, expr = self.expressions[index]

        if indent != expected_indent or expr[0] != "while":
            raise RuntimeError("Indentation error: expected while loop")
        
        body_start = index + 1

        index = self.validate_block(body_start, end, expected_indent + 1)

        return index
    
    def validate_function_definition(self, start, end, expected_indent):
        index = start

        indent, expr = self.expressions[index]
        if indent != expected_indent or expr[0] != "def":
            raise RuntimeError("Indentation error: expected function definition")

        body_start = index + 1
    
        if body_start >= end:
            raise RuntimeError("Indentation error: expected indented block")

        next_indent, _ = self.expressions[body_start]
        if next_indent != expected_indent + 1:
            raise RuntimeError("Indentation error: expected indented block")
        
        body_end = self.validate_block(body_start, end, expected_indent + 1)
        return body_end

    def validate_if_chain(self, start, end, header_indent):
        index = start
        saw_else = False

        while index < end:
            indent, expr = self.expressions[index]
            if indent != header_indent or expr[0] not in ("if", "elif", "else"):
                break

            branch_type = expr[0]

            if branch_type == "if" and index != start:
                raise RuntimeError("Indentation error: unexpected if in conditional chain")

            if branch_type == "elif" and saw_else:
                raise RuntimeError("Indentation error: elif after else")

            if branch_type == "else":
                if saw_else:
                    raise RuntimeError("Indentation error: multiple else branches")
                saw_else = True

            body_start = index + 1
            if body_start >= end:
                raise RuntimeError("Indentation error: expected indented block")

            next_indent, _ = self.expressions[body_start]
            if next_indent != header_indent + 1:
                raise RuntimeError("Indentation error: expected indented block")

            body_end = self.validate_block(body_start, end, header_indent + 1)
            index = body_end

            if index >= end:
                break

            next_indent, next_expr = self.expressions[index]
            if next_indent != header_indent or next_expr[0] not in ("elif", "else"):
                break

        return index

    def eval_range(self, start, end):
        results = []
        index = start

        while index < end:
            _, expr = self.expressions[index]

            if expr[0] == "if":
                branch_results, index = self.eval_if_chain(index, end)
                results.extend(branch_results)
            elif expr[0] == "while":
                cond_expr = expr[1]
                body_start = index + 1
                body_end = body_start

                while body_end < end:
                    body_indent, _ = self.expressions[body_end]
                    if body_indent <= self.expressions[index][0]:
                        break
                    body_end += 1

                while_results = self.eval_while_loop(cond_expr, body_start, body_end)
                results.extend(while_results)
                index = body_end
            elif expr[0] == "for":
                var_name = expr[1]
                iterable_expr = expr[2]
                body_start = index + 1
                body_end = body_start

                while body_end < end:
                    body_indent, _ = self.expressions[body_end]
                    if body_indent <= self.expressions[index][0]:
                        break
                    body_end += 1
                loop_results = self.eval_for_loop(var_name, iterable_expr, body_start, body_end)
                results.extend(loop_results)
                index = body_end
            elif expr[0] == "def":
                index = self.eval_function_definition(index, end)
            elif expr[0] in ("elif", "else"):
                raise RuntimeError("Unexpected conditional branch without matching if")
            else:
                results.append(self.eval_expr(expr))
                index += 1

        return results, index

    def eval_if_chain(self, start, limit):
        header_indent, _ = self.expressions[start]
        branches = []
        index = start

        while index < limit:
            indent, expr = self.expressions[index]
            if indent != header_indent or expr[0] not in ("if", "elif", "else"):
                break

            branch_type = expr[0]
            condition = expr[1] if branch_type in ("if", "elif") else None
            body_start = index + 1
            body_end = body_start

            while body_end < limit:
                body_indent, _ = self.expressions[body_end]
                if body_indent <= header_indent:
                    break
                body_end += 1

            branches.append((branch_type, condition, body_start, body_end))
            index = body_end

            if index >= limit:
                break

            next_indent, next_expr = self.expressions[index]
            if next_indent != header_indent or next_expr[0] not in ("elif", "else"):
                break

        results = []
        matched = False

        for branch_type, condition, body_start, body_end in branches:
            if matched:
                break

            should_run = False

            if branch_type == "if":
                should_run = self.eval_expr(condition)
            elif branch_type == "elif":
                should_run = not matched and self.eval_expr(condition)
            else:
                should_run = not matched

            if should_run:
                branch_results, _ = self.eval_range(body_start, body_end)
                results.extend(branch_results)
                matched = True

        return results, index
    
    def eval_function_definition(self, start, limit):
        indent, expr = self.expressions[start]
        if expr[0] != "def":
            raise RuntimeError("Expected function definition")

        func_name = expr[1]
        body_start = start + 1
        body_end = body_start

        while body_end < limit:
            body_indent, _ = self.expressions[body_end]
            if body_indent <= indent:
                break
            body_end += 1

        function_body = self.expressions[body_start:body_end]

        def function(*args):
            body_evaluator = Evaluator(function_body)

            if len(args) != len(expr[2]):
                raise RuntimeError(f"Expected {len(expr[2])} arguments but got {len(args)}")
            
            body_evaluator.environment = {**self.environment, **dict(zip(expr[2], args))}

            try:
                results, _ = body_evaluator.eval_range(0, len(function_body))
                return results[-1] if results else None
            except Return as r:
                return r.value

        self.environment[func_name] = function
        return body_end
    
    def eval_function_call(self, func_name, arg_exprs):
        if func_name not in self.environment or not callable(self.environment[func_name]):
            raise RuntimeError(f"Undefined function: {func_name}")
        
        try:
            func = self.environment[func_name]
            args = [self.eval_expr(arg) for arg in arg_exprs]
            return func(*args)
        except Return as r:
            return r.value
        
    def eval_for_loop(self, var_name, iterable_expr, body_start, body_end):       
        iterable = self.eval_expr(iterable_expr)
        if not hasattr(iterable, "__iter__"):
            raise RuntimeError(f"Object of type '{type(iterable).__name__}' is not iterable")

        results = []
        for item in iterable:
            self.environment[var_name] = item
            body_results, _ = self.eval_range(body_start, body_end)
            results.extend(body_results)

        del self.environment[var_name]
        return results
    
    def eval_while_loop(self, cond_expr, body_start, body_end):
        if cond_expr[0] != "binop":
            raise RuntimeError("Expected binary expression as while loop condition")

        results = []
        while self.eval_expr(cond_expr):
            body_results, _ = self.eval_range(body_start, body_end)
            results.extend(body_results)
        return results

    def eval_expr(self, expr):
        if expr[0] == "number":
            return expr[1]
        elif expr[0] == "ident":
            if expr[1] in self.environment:
                return self.environment[expr[1]]
            raise RuntimeError(f"Undefined variable: {expr[1]}")
        elif expr[0] == "return":
            if expr[1] is None:
                raise Return(None)
            value = self.eval_expr(expr[1])
            raise Return(value)
        elif expr[0] == "binop":
            op = expr[1]
            left = self.eval_expr(expr[2])
            right = self.eval_expr(expr[3])
            if op == "+":
                return left + right
            if op == "+=":
                if not isinstance(expr[2], tuple) or expr[2][0] != "ident":
                    raise RuntimeError("Left-hand side of += must be a variable")
                var_name = expr[2][1]
                if var_name not in self.environment:
                    raise RuntimeError(f"Undefined variable: {var_name}")
                self.environment[var_name] += right
                return self.environment[var_name]
            elif op == "-":
                return left - right
            elif op == "-=":
                if not isinstance(expr[2], tuple) or expr[2][0] != "ident":
                    raise RuntimeError("Left-hand side of -= must be a variable")
                var_name = expr[2][1]
                if var_name not in self.environment:
                    raise RuntimeError(f"Undefined variable: {var_name}")
                self.environment[var_name] -= right
                return self.environment[var_name]
            elif op == "*":
                return left * right
            elif op == "*=":
                if not isinstance(expr[2], tuple) or expr[2][0] != "ident":
                    raise RuntimeError("Left-hand side of *= must be a variable")
                var_name = expr[2][1]
                if var_name not in self.environment:
                    raise RuntimeError(f"Undefined variable: {var_name}")
                self.environment[var_name] *= right
                return self.environment[var_name]
            elif op == "/":
                return left / right
            elif op == "/=":
                if not isinstance(expr[2], tuple) or expr[2][0] != "ident":
                    raise RuntimeError("Left-hand side of /= must be a variable")
                var_name = expr[2][1]
                if var_name not in self.environment:
                    raise RuntimeError(f"Undefined variable: {var_name}")
                self.environment[var_name] /= right
                return self.environment[var_name]
            elif op == "==":
                return left == right
            elif op == "!=":
                return left != right
            elif op == "<":
                return left < right
            elif op == ">":
                return left > right
            elif op == "<=":
                return left <= right
            elif op == ">=":
                return left >= right
            elif op == "and":
                return left and right
            elif op == "or":
                return left or right
        elif expr[0] == "inlinecond":
            condition = self.eval_expr(expr[1])
            if condition:
                return self.eval_expr(expr[2])
            else:
                return self.eval_expr(expr[3])
        elif expr[0] == "call":
            return self.eval_function_call(expr[1], expr[2])
        elif expr[0] == "assign":
            var_name = expr[1]
            value = self.eval_expr(expr[2])

            self.environment[var_name] = value
            return None
        elif expr[0] == "string":
            return expr[1]
        elif expr[0] == "fstring":
            parts = []
            for kind, val in expr[1]:
                if kind == "string":
                    parts.append(val)
                elif kind == "expr":
                    parts.append(str(self.eval_expr(val)))
            return ''.join(parts)
        elif expr[0] == "list":
            return [self.eval_expr(item) for item in expr[1]]
        # elif expr[0] == "print":
        #     value = self.eval_expr(expr[1])
        #     print(value)
        #     return None
        else:
            raise RuntimeError(f"Unknown expression type: {expr[0]}")
            