# Python Evaluator

import platform
from pathlib import Path
import os
import importlib
import types

current_os = platform.system()

clear_arg = "cls" if current_os == "Windows" else "clear"

class Module:
    def __init__(self, name, scope):
        self.name = name
        self.scope = scope
    
    def get_attr(self, attr):
        if attr in self.scope:
            return self.scope[attr]
        raise RuntimeError(f"Module '{self.name}' has no attribute '{attr}'")

class Class:
            def __init__(self, name, scope):
                self.name = name
                self.scope = scope

            def instantiate(self):
                # copy class scope into instance attributes
                return Object(self.name, dict(self.scope))
    
class Object:
    def __init__(self, type_name, attributes):
        self.type_name = type_name
        self.attributes = attributes
    
    def get_attr(self, attr):
        if attr in self.attributes:
            val = self.attributes[attr]
            # If the attribute is an interpreter-defined function, bind `self` as first arg
            if isinstance(val, types.FunctionType):
                def bound(*args, __val=val, __self=self):
                    return __val(__self, *args)
                return bound
            return val
        raise RuntimeError(f"Object of type '{self.type_name}' has no attribute '{attr}'")
    
    def set_attr(self, attr, value):
        self.attributes[attr] = value

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
            elif expr[0] == "class_def":
                index = self.validate_class_definition(index, end, expected_indent)
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

    def validate_class_definition(self, start, end, expected_indent):
        index = start

        indent, expr = self.expressions[index]
        if indent != expected_indent or expr[0] != "class_def":
            raise RuntimeError("Indentation error: expected class definition")

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
            elif expr[0] == "class_def":
                index = self.eval_class_definition(index, end)
            elif expr[0] == "import":
                module_name = expr[1]
                as_name = expr[2] if len(expr) > 2 else None
                self.eval_import(module_name, as_name)
                index += 1
            elif expr[0] == "from_import":
                module_name = expr[1]
                attr_name = expr[2]
                as_name = expr[3] if len(expr) > 3 else None
                self.eval_from_import(module_name, attr_name, as_name)
                index += 1
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
    
    def eval_function_call(self, func_expr, arg_exprs):
        func = self.eval_expr(func_expr)
        args = [self.eval_expr(arg) for arg in arg_exprs]

        # Class instantiation
        if hasattr(func, 'instantiate'):
            instance = func.instantiate()
            # Call __init__ if present
            init = instance.attributes.get('__init__')
            if init and callable(init):
                init(instance, *args)
            return instance

        if not callable(func):
            raise RuntimeError(f"Undefined function: {func_name}")
            
        try:
            return func(*args)
        except Return as r:
            return r.value

    def eval_class_definition(self, start, limit):
        indent, expr = self.expressions[start]
        if expr[0] != "class_def":
            raise RuntimeError("Expected class definition")

        class_name = expr[1]
        body_start = start + 1
        body_end = body_start

        while body_end < limit:
            body_indent, _ = self.expressions[body_end]
            if body_indent <= indent:
                break
            body_end += 1

        class_body = self.expressions[body_start:body_end]

        # Evaluate class body in its own evaluator to collect methods/attrs
        class_scope = {}
        class_evaluator = Evaluator(class_body)
        class_evaluator.environment = {}
        class_evaluator.eval_range(0, len(class_body))
        class_scope.update(class_evaluator.environment)

        cls = Class(class_name, class_scope)
        self.environment[class_name] = cls
        return body_end
        
    def eval_for_loop(self, target_expr, iterable_expr, body_start, body_end):       
        iterable = self.eval_expr(iterable_expr)
        if not hasattr(iterable, "__iter__"):
            raise RuntimeError(f"Object of type '{type(iterable).__name__}' is not iterable")

        target_names = list(dict.fromkeys(self._collect_target_names(target_expr)))
        missing = object()
        previous_bindings = {
            name: self.environment.get(name, missing)
            for name in target_names
        }

        results = []
        for item in iterable:
            self._bind_target(target_expr, item)
            body_results, _ = self.eval_range(body_start, body_end)
            results.extend(body_results)

        for name in target_names:
            previous = previous_bindings[name]
            if previous is missing:
                self.environment.pop(name, None)
            else:
                self.environment[name] = previous

        return results

    def eval_import(self, module_name, as_name=None):
        if module_name in self.environment:
            return self.environment[module_name]

        try:
            module_scope = importlib.import_module(module_name).__dict__
            module = Module(module_name, module_scope)
            self.environment[module_name] = module
            if as_name:
                self.environment[as_name] = module
            return module
        except ImportError:
            raise RuntimeError(f"Module '{module_name}' not found")
    
    def eval_from_import(self, module_name, attr_name, as_name=None):
        module = self.eval_import(module_name)

        if attr_name not in module.scope:
            raise RuntimeError(f"Module '{module_name}' has no attribute '{attr_name}'")

        self.environment[attr_name] = module.scope[attr_name]
        if as_name:
            self.environment[as_name] = module.scope[attr_name]
        return module.scope[attr_name]

    def _resolve_attr_on(self, obj, attr_name):
        """Resolve attribute `attr_name` on an evaluated object `obj`.

        Handles interpreter wrappers (`Module`, `Object`) first, then
        falls back to Python's `getattr` for native objects. Raises a
        consistent RuntimeError when the attribute is missing.
        """
        if isinstance(obj, Module) or isinstance(obj, Object):
            return obj.get_attr(attr_name)

        if hasattr(obj, attr_name):
            return getattr(obj, attr_name)

        raise RuntimeError(f"Object of type '{type(obj).__name__}' has no attribute '{attr_name}'")

    def _collect_target_names(self, target_expr):
        if target_expr[0] == "ident":
            return [target_expr[1]]

        if target_expr[0] == "tuple":
            names = []
            for item in target_expr[1]:
                names.extend(self._collect_target_names(item))
            return names

        raise RuntimeError("Expected unpack target")

    def _bind_target(self, target_expr, value):
        if target_expr[0] == "ident":
            self.environment[target_expr[1]] = value
            return

        if target_expr[0] != "tuple":
            raise RuntimeError("Expected unpack target")

        try:
            values = list(value)
        except TypeError:
            raise RuntimeError("Cannot unpack non-iterable object")

        if len(values) != len(target_expr[1]):
            raise RuntimeError(
                f"Expected {len(target_expr[1])} values to unpack but got {len(values)}"
            )

        for subtarget, subvalue in zip(target_expr[1], values):
            self._bind_target(subtarget, subvalue)

    def eval_set_attr(self, obj_expr, attr_name, value_expr):
        obj = self.eval_expr(obj_expr)

        if isinstance(obj, Object):
            obj.set_attr(attr_name, self.eval_expr(value_expr))
        else:
            raise RuntimeError(f"Object of type '{type(obj).__name__}' has no attribute '{attr_name}'")

    def eval_while_loop(self, cond_expr, body_start, body_end):
        if cond_expr[0] not in ("binop", "inlinecond", "call", "ident", "number", "string", "boolean", "fstring", "list"):
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
        elif expr[0] == "attr_call":
            target = self.eval_expr(expr[1])
            func = self._resolve_attr_on(target, expr[2])

            if not callable(func):
                raise RuntimeError(f"Attribute '{expr[2]}' is not callable")

            args = [self.eval_expr(arg) for arg in expr[3]]
            return func(*args)
        elif expr[0] == "get_attr":
            obj = self.eval_expr(expr[1])
            return self._resolve_attr_on(obj, expr[2])
        elif expr[0] == "set_attr":
            self.eval_set_attr(expr[1], expr[2], expr[3])
            return None
        elif expr[0] == "assign":
            value = self.eval_expr(expr[2])
            self._bind_target(expr[1], value)
            return None
        elif expr[0] == "string":
            return expr[1]
        elif expr[0] == "fstring":
            parts = []
            for element in expr[1]:
                if len(element) == 2:
                    kind, val = element
                    format_spec = None
                else:
                    kind, val, format_width, format_precision, format_type = element
                if kind == "string":
                    parts.append(val)
                elif kind == "expr":
                    parts.append(str(self.eval_expr(val)))
                elif kind == "format_spec_expr":
                    if format_width:
                        width = self.eval_expr(format_width)
                    else:
                        width = None
                    if format_precision:
                        precision = self.eval_expr(format_precision)
                    else:
                        precision = None
                    format_spec = ""
                    if width is not None:
                        format_spec += f"{width}"
                    if precision is not None:
                        format_spec += f".{precision}"
                    if format_type is not None:
                        format_spec += f"{format_type}"
                    formatted = format(self.eval_expr(val), format_spec)
                    parts.append(formatted)
            return ''.join(parts)
        elif expr[0] == "list":
            return [self.eval_expr(item) for item in expr[1]]
        elif expr[0] == "dict":
            return {self.eval_expr(key): self.eval_expr(value) for key, value in expr[1]}
        elif expr[0] == "tuple":
            return tuple(self.eval_expr(item) for item in expr[1])
        elif expr[0] == "list_access":
            list_obj = self.eval_expr(expr[1])

            if len(expr) == 4:
                start = self.eval_expr(expr[2])
                end = self.eval_expr(expr[3])
                try:
                    return list_obj[start:end]
                except (IndexError, KeyError, TypeError) as e:
                    raise RuntimeError(f"Invalid list access: {e}")
            if len(expr) == 5:
                start = self.eval_expr(expr[2])
                end = self.eval_expr(expr[3])
                step = self.eval_expr(expr[4])
                try:
                    return list_obj[start:end:step]
                except (IndexError, KeyError, TypeError) as e:
                    raise RuntimeError(f"Invalid list access: {e}")
            try:
                index = self.eval_expr(expr[2])
                return list_obj[index]
            except (IndexError, KeyError, TypeError) as e:
                raise RuntimeError(f"Invalid list access: {e}")
        elif expr[0] == "boolean":
            return expr[1]
        # elif expr[0] == "print":
        #     value = self.eval_expr(expr[1])
        #     print(value)
        #     return None
        else:
            raise RuntimeError(f"Unknown expression type: {expr[0]}")
            