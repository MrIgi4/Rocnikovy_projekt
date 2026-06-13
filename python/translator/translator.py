import ast

from translator.translation import Translation


class Translator(ast.NodeVisitor):
    """Translates Python code to c++ code using the method translate(str pytonCode) and stores it in self.translation."""

    def __init__(self, debug: bool = False):
        self.is_debugging = debug
        self.abstract_syntax_tree = None
        self.translation = Translation()
        self.variables = {}
        # List of variables by indentation for deletion after their scope is exited
        # Initialized with global scope
        self.scoped_variables: list[list[str]] = [[]]
        self.classes: list[str] = []
        self.class_variables: dict[str, dict[str, str]] = {}

    # _ at the start of a method means it's not public
    def _create_type_annotation(self, value) -> str:
        """Creates and returns type annotation for assignment of variables, e.g. int."""
        if isinstance(value, ast.Name):
            return self.variables.get(value.id)

        elif isinstance(value, ast.Constant):
            string = str(type(value.value))
            # Remove irrelevant part of type annotation
            variable_type = string[8:len(string) - 2]
            return "string" if variable_type == "str" else variable_type

        elif isinstance(value, ast.BinOp):
            return self._create_type_annotation(value.left)

        elif isinstance(value, ast.UnaryOp):
            return self._create_type_annotation(value.operand)

        elif isinstance(value, ast.Call):
            if isinstance(value.func, ast.Name) and value.func.id in self.classes:
                return value.func.id
            return "auto"

        elif isinstance(value, ast.Attribute):
            if isinstance(value.value, ast.Name) and value.value.id == "self":
                if self.translation.current_class and self.translation.current_class in self.class_variables:
                    if value.attr in self.class_variables[self.translation.current_class]:
                        return self.class_variables[self.translation.current_class][value.attr]
            else:
                obj_type = self._create_type_annotation(value.value)
                if obj_type in self.class_variables and value.attr in self.class_variables[obj_type]:
                    return self.class_variables[obj_type][value.attr]

            var_type = self.variables.get(value.attr)
            if var_type is not None:
                return var_type

            return self._raise_or_auto(value)
        elif isinstance(value, ast.List):
            self.translation.imports.add("vector")
            if len(value.elts) == 0:
                return "vector<auto>"
            firstType = self._create_type_annotation(value.elts[0])
            for elt in value.elts[1:]:
                if self._create_type_annotation(elt) != firstType:
                    return "vector<auto>"
            return "vector<" + firstType + ">"

        # TODO low priority
        elif isinstance(value, ast.Tuple):
            return self._raise_or_auto(value)
        elif isinstance(value, ast.Dict):
            return self._raise_or_auto(value)
        elif isinstance(value, ast.Set):
            return self._raise_or_auto(value)
        elif isinstance(value, ast.Compare):
            return "bool"
        else:
            return self._raise_or_auto(value)

    def _translate_expression(self, value) -> str:
        """Evaluates an expression, translates it into c++ and returns it."""
        if isinstance(value, ast.Name):
            return value.id

        elif isinstance(value, ast.Constant):
            if isinstance(value.value, str):
                return "\"" + str(value.value) + "\""
            elif isinstance(value.value, bool):
                return "true" if value.value else "false"
            return str(value.value)

        elif isinstance(value, ast.BinOp):
            return self._translate_expression(value.left) + " " + self._translate_expression(
                value.op) + " " + self._translate_expression(value.right)

        elif isinstance(value, ast.UnaryOp):
            return self._translate_expression(value.op) + self._translate_expression(value.operand)

        elif isinstance(value, ast.Compare):
            return self._translate_expression(value.left) + " " + self._translate_expression(
                value.ops[0]) + " " + self._translate_expression(value.comparators[0])

        elif isinstance(value, ast.Add):
            return "+"
        elif isinstance(value, ast.Sub) or isinstance(value, ast.USub):
            return "-"
        elif isinstance(value, ast.Mult):
            return "*"
        elif isinstance(value, ast.Div):
            return "/"
        elif isinstance(value, ast.BitOr):
            return "|"
        elif isinstance(value, ast.BitXor):
            return "^"
        elif isinstance(value, ast.BitAnd):
            return "&"
        elif isinstance(value, ast.Eq):
            return "=="
        elif isinstance(value, ast.Lt):
            return "<"
        elif isinstance(value, ast.LtE):
            return "<="
        elif isinstance(value, ast.Gt):
            return ">"
        elif isinstance(value, ast.GtE):
            return ">="
            # TODO check is
            ##elif isinstance(value, ast.Is):
            return "is"
            ##elif isinstance(value, ast.IsNot):
            return "is not"
        elif isinstance(value, ast.Not):
            return "!"

        elif isinstance(value, ast.Call):
            expression = ""
            if isinstance(value.func, ast.Attribute):
                if isinstance(value.func.value, ast.Name) and value.func.value.id == "self":
                    expression = "this->" + value.func.attr
                else:
                    expression = self._translate_expression(value.func.value) + "." + value.func.attr
            elif isinstance(value.func, ast.Name):
                expression = str(value.func.id)
            expression += "("
            for i in range(len(value.args)):
                arg = value.args[i]
                expression += self._translate_expression(arg)
                if i != len(value.args) - 1:
                    expression += ", "
            expression += ")"
            return expression

        elif isinstance(value, ast.Attribute):
            if isinstance(value.value, ast.Name) and value.value.id == "self":
                return "this->" + value.attr
            else:
                # Handle class variables
                return self._translate_expression(value.value) + "." + value.attr

        elif isinstance(value, ast.List):
            self.translation.imports.add("vector")
            if len(value.elts) == 0:
                return "vector<auto>()"

            expression = "{"
            for i in range(len(value.elts)):
                expression += self._translate_expression(value.elts[i])
                if i != len(value.elts) - 1:
                    expression += ", "
            expression += "}"
            return expression
            # May use this code later:
            #first_type = self.createTypeAnnotation(value.elts[0])
            #for elt in value.elts[1:]:
            #    if self.createTypeAnnotation(elt) != first_type:
            #        return "vector<auto>()"
            #
            #return "vector<" + first_type + ">()"
        # TODO low priority
        elif isinstance(value, ast.Tuple):
            self.translation.imports.add("tuple")
            return self._raise_or_auto(value)
        elif isinstance(value, ast.Dict):
            self.translation.imports.add("map")
            return self._raise_or_auto(value)
        elif isinstance(value, ast.Set):
            self.translation.imports.add("set")
            return self._raise_or_auto(value)
        else:
            return self._raise_or_auto(value)

    def _assign_target(self, target, variable_type: str, is_reassignment: bool) -> None:
        self.variables[target.id] = variable_type
        if not is_reassignment:
            self.scoped_variables[-1].append(target.id)

    def _raise_or_auto(self, node) -> str:
        if self.is_debugging:
            raise TypeError(f"Could not infer type for node '{type(node).__name__}' at line {getattr(node, 'lineno', 'unknown')}")
        return "auto"

    def _emit_indentation(self):
        """Calculates and emits the correct whitespace tokens for the current scope."""
        base_indent = 1 if self.translation.to_main else 0
        total_indent = base_indent + self.translation.indentation

        indent_str = "    " * total_indent
        if indent_str:
            self.translation.emit(indent_str, "indentation")

    def _emit_semicolon(self):
        self.translation.emit(";\n", "semicolon")

    def _emit_space(self):
        self.translation.emit(" ", "space")

    def _enter_block(self):
        self.scoped_variables.append([])
        self.translation.indentation += 1

    def _exit_block(self):
        for variable in self.scoped_variables[self.translation.indentation]:
            if variable in self.variables:
                self.variables.pop(variable)
        self.scoped_variables.pop()
        self.translation.indentation -= 1


    # @Override of functions from ast module
    def visit(self, node) -> None:
        """
        Overrides the default AST visitor to automatically handle
        indentation, semicolons, and newlines for statement nodes.
        """
        is_statement = isinstance(node, ast.stmt)
        needs_semicolon = not isinstance(node, (
            ast.For, ast.While, ast.If, ast.FunctionDef, ast.ClassDef
        ))
        is_scope_node = isinstance(node, (ast.FunctionDef, ast.ClassDef))

        if is_statement and not is_scope_node:
            self._emit_indentation()

        super().visit(node)

        if is_statement and not is_scope_node:
            if needs_semicolon:
                self._emit_semicolon()
            elif is_statement:
                self.translation.emit("\n", "newline")

    def visit_Expr(self, node) -> None:
        translated_expression = self._translate_expression(node.value)
        if translated_expression:
            self.translation.emit(translated_expression, "expression")

    def visit_Assign(self, node) -> None:
        variable_type = self._create_type_annotation(node.value)
        value_string = self._translate_expression(node.value)

        # Process each target individually to support chained assignments (differ in Python and C++)
        for target in node.targets:
            if isinstance(target, ast.Name):
                is_reassignment = target.id in self.variables
                self._assign_target(target, variable_type, is_reassignment)

                if not is_reassignment:
                    self.translation.emit(variable_type, "type annotation")
                    self._emit_space()

                self.translation.emit(target.id, "variable declaration")
                self.translation.emit(" = ", "assignment operator")
                self.translation.emit(value_string, "expression")

            elif isinstance(target, ast.Attribute):
                # Attributes (like self.hp or player.hp)
                target_string = self._translate_expression(target)

                self.translation.emit(target_string, "variable declaration")
                self.translation.emit(" = ", "assignment operator")
                self.translation.emit(value_string, "expression")

            elif isinstance(target, ast.Tuple):
                # Handle tuple unpacking targets (like x, y = ...)
                for element in target.elts:
                    if isinstance(element, ast.Name):
                        is_reassignment = element.id in self.variables
                        self._assign_target(element, variable_type, is_reassignment)

                        if not is_reassignment:
                            self.translation.emit(variable_type, "type annotation")
                            self._emit_space()

                        self.translation.emit(element.id, "variable declaration")
                        self.translation.emit(" = ", "assignment operator")
                        self.translation.emit(value_string, "expression")
                        if element != target.elts[-1]:
                            self._emit_semicolon()
                            self._emit_indentation()

    def visit_AugAssign(self, node) -> None:
        translation = node.target.id
        translation += " " + self._translate_expression(node.op) + "="
        translation += " " + self._translate_expression(node.value)
        self.translation.emit(translation, "augmented assignment")

    def visit_If(self, node, is_elif=False) -> None:
        expression = self._translate_expression(node.test)
        keyword = "else if" if is_elif else "if"

        self.translation.emit(keyword + " (" + expression + ")", keyword)
        self._emit_space()
        self.translation.emit("{\n", "start bracket - if")

        self._enter_block()
        for stmt in node.body:
            self.visit(stmt)
        self._exit_block()

        self._emit_indentation()
        if is_elif:
            self.translation.emit("}\n", "end bracket - elif")
            self._emit_indentation()
        else:
            self.translation.emit("}", "end bracket - if")
            if node.orelse:
                self.translation.emit("\n", "newline")
                self._emit_indentation()

        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                # Recursive elif
                self.visit_If(node.orelse[0], True)
            else:
                self.translation.emit("else", "else")
                self._emit_space()
                self.translation.emit("{\n", "start bracket - else")

                self._enter_block()
                for stmt in node.orelse:
                    self.visit(stmt)
                self._exit_block()

                self._emit_indentation()
                self.translation.emit("}", "end bracket - else")

    def handle_range(self, args, new_variable: str) -> None:
        start = "0"
        step = 1
        if len(args) > 1:
            start = self._translate_expression(args[0])
            end = self._translate_expression(args[1])
        else:
            end = self._translate_expression(args[0])
        if len(args) > 2:
            step = self._translate_expression(args[2])
        if step == 1 or step == "1":
            step_increase = new_variable + "++"
        else:
            step_increase = new_variable + " += " + step

        self.translation.emit("for (int " + new_variable + " = " + start + ";" +
                              " " + new_variable + " < " + end + ";" +
                              " " + step_increase +
                              ")", "for - range")
        self._emit_space()
        self.translation.emit("{\n", "start bracket - for")

    def handle_len(self, args, new_variable: str) -> None:
        self.translation.emit("for (int " + new_variable + " = 0;" +
                              " " + new_variable + " < " + self._translate_expression(args[0]) + ";" +
                              " " + new_variable + "++)", "for - len")
        self._emit_space()
        self.translation.emit("{\n", "start bracket - for")

    def visit_For(self, node) -> None:
        new_variable = self._translate_expression(node.target)
        iterable = node.iter
        self.variables[new_variable] = self._create_type_annotation(node.target)

        if (isinstance(iterable, ast.Call) and
                isinstance(iterable.func, ast.Name) and
                iterable.func.id == "range"):
            self.handle_range(iterable.args, new_variable)
        elif (isinstance(iterable, ast.Call) and
              isinstance(iterable.func, ast.Name) and
              iterable.func.id == "len"):
            self.handle_len(iterable.args, new_variable)
        else:
            # I expect it to be of form "iterable<type>"
            iterable_type = self._create_type_annotation(iterable)
            new_variable_type = iterable_type[iterable_type.find("<") + 1:-1]
            self.translation.emit("for (" + new_variable_type + " " + new_variable + " : " +
                                  self._translate_expression(iterable) + ")", "for")
            self._emit_space()
            self.translation.emit("{\n", "start bracket - for")

        self._enter_block()
        for stmt in node.body:
            self.visit(stmt)
        self._exit_block()

        self._emit_indentation()
        self.translation.emit("}", "end bracket - for")

    def visit_Break(self, node) -> None:
        self.translation.emit("break", "break")

    def visit_Continue(self, node) -> None:
        self.translation.emit("continue", "continue")

    def visit_While(self, node) -> None:
        expression = self._translate_expression(node.test)
        self.translation.emit("while (" + expression + ")", "while")
        self._emit_space()
        self.translation.emit("{\n", "start bracket - while")

        self._enter_block()
        for stmt in node.body:
            self.visit(stmt)
        self._exit_block()

        self._emit_indentation()
        self.translation.emit("}", "end bracket - while")

    def visit_FunctionDef(self, node) -> None:
        previous_scope = self.translation.to_main
        self.translation.to_main = False
        class_name = node.name

        self._emit_indentation()

        is_initializer = node.name == "__init__" and self.translation.current_class is not None

        if is_initializer:
            class_name = self.translation.current_class
        else:
            # Handle return type
            return_type = "auto"
            if node.returns:
                if isinstance(node.returns, ast.Name):
                    return_type = node.returns.id
                    if return_type == "str":
                        return_type = "string"
                        self.translation.imports.add("string")
                elif isinstance(node.returns, ast.Constant) and node.returns.value is None:
                    return_type = "void"
            self.translation.emit(return_type, "return type")
            self._emit_space()

        # Handle arguments
        arg_list = []
        for arg in node.args.args:
            if arg.arg == "self":
                continue
            arg_type = "auto"
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    arg_type = arg.annotation.id
                    if arg_type == "str":
                        arg_type = "string"
                        self.translation.imports.add("string")
                else:
                    # Shouldn't happen
                    self._raise_or_auto(arg.annotation)
            arg_list.append(arg_type + " " + str(arg.arg))
            self.variables[arg.arg] = arg_type

        args = ", ".join(arg_list)
        self.translation.emit(class_name + "(" + args + ")",
                              "function" + " - initializer" if is_initializer else "")
        self._emit_space()
        self.translation.emit("{\n", "start bracket - function")

        self._enter_block()

        for arg in node.args.args:
            if arg.arg != "self":
                self.scoped_variables[-1].append(str(arg.arg))

        for stmt in node.body:
            self.visit(stmt)
        self._exit_block()

        self._emit_indentation()
        self.translation.emit("}", "end bracket - function")
        self.translation.emit("\n", "newline")

        self.translation.to_main = previous_scope

    def visit_Return(self, node) -> None:
        if node.value:
            self.translation.emit("return " + self._translate_expression(node.value), "return")
        else:
            self.translation.emit("return", "return")

    def visit_ClassDef(self, node):
        self.classes.append(node.name)
        self.class_variables[node.name] = {}
        previous_scope = self.translation.to_main
        previous_class = self.translation.current_class
        self.translation.to_main = False
        self.translation.current_class = node.name

        self._emit_indentation()
        self.translation.emit("class " + node.name, "class")
        self._emit_space()
        self.translation.emit("{\n", "start bracket - class")

        self._emit_indentation()
        self.translation.emit("public:\n", "access modifier")
        self._enter_block()

        temporary_args_to_clean = []
        # Pre-pass for class variables
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                # Add __init__ arguments to variables temporarily
                for arg in stmt.args.args:
                    if arg.arg != "self":
                        argType = "auto"
                        if arg.annotation and isinstance(arg.annotation, ast.Name):
                            argType = arg.annotation.id
                            if argType == "str":
                                argType = "string"
                        self.variables[arg.arg] = argType
                        temporary_args_to_clean.append(arg.arg)

                for sub_stmt in stmt.body:
                    if isinstance(sub_stmt, ast.Assign):
                        for target in sub_stmt.targets:
                            if isinstance(target, ast.Attribute) and isinstance(target.value,
                                    ast.Name) and target.value.id == "self":
                                var_type = self._create_type_annotation(sub_stmt.value)
                                var_name = target.attr
                                if var_type is None:
                                    var_type = self._raise_or_auto(sub_stmt.value)

                                self._emit_indentation()
                                self.translation.emit(var_type, "type annotation")
                                self._emit_space()
                                self.translation.emit(var_name, "class variable")
                                self._emit_semicolon()

                                self.class_variables[self.translation.current_class][var_name] = var_type

        if len(self.class_variables[self.translation.current_class]) > 0:
            self.translation.emit("\n", "newline")

        for arg in temporary_args_to_clean:
            if arg in self.variables:
                self.variables.pop(arg)

        for stmt in node.body:
            self.visit(stmt)
        self._exit_block()

        self._emit_indentation()
        self.translation.emit("}", "end bracket - class")
        self._emit_semicolon()

        self.translation.to_main = previous_scope
        self.translation.current_class = previous_class


    def translate(self, text: str) -> None:
        # TODO Syntax Error handling
        self.abstract_syntax_tree = ast.parse(text)
        self.visit(self.abstract_syntax_tree)
        self.translation.wrap_main()
        self.translation.final_add_imports()
        self.translation.final_combine_global_and_main()


    # Debugging functions
    def print_ast(self, text: str | None) -> None:
        if self.abstract_syntax_tree:
            print(self.abstract_syntax_tree)
        else:
            self.abstract_syntax_tree = ast.parse(text)
            print(ast.dump(self.abstract_syntax_tree, indent=4))

    def print_code(self) -> None:
        print(self.translation.print_code())
