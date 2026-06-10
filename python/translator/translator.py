import ast

from translator.translation import Translation


class Translator(ast.NodeVisitor):
    """Translates Python code to c++ code using the method translate(str pytonCode) and stores it in self.translation."""

    def __init__(self, debug: bool = False):
        self.isDebugging = debug
        self.abstractSyntaxTree = None
        self.translation = Translation()
        self.variables = {}
        # List of variables by indentation for deletion after their scope is exited
        # Initialized with global scope
        self.scopedVariables: list[list[str]] = [[]]
        self.classes: list[str] = []
        self.classVariables: dict[str, dict[str, str]] = {}

    def createTypeAnnotation(self, value) -> str:
        """Creates and returns type annotation for assignment of variables, e.g. int."""
        if isinstance(value, ast.Name):
            return self.variables.get(value.id)

        elif isinstance(value, ast.Constant):
            string = str(type(value.value))
            # Remove irrelevant part of type annotation
            variable_type = string[8:len(string) - 2]
            return "string" if variable_type == "str" else variable_type

        elif isinstance(value, ast.BinOp):
            return self.createTypeAnnotation(value.left)

        elif isinstance(value, ast.UnaryOp):
            return self.createTypeAnnotation(value.operand)

        elif isinstance(value, ast.Call):
            if isinstance(value.func, ast.Name) and value.func.id in self.classes:
                return value.func.id
            return "auto"

        elif isinstance(value, ast.Attribute):
            if isinstance(value.value, ast.Name) and value.value.id == "self":
                if self.translation.currentClass and self.translation.currentClass in self.classVariables:
                    if value.attr in self.classVariables[self.translation.currentClass]:
                        return self.classVariables[self.translation.currentClass][value.attr]
            else:
                obj_type = self.createTypeAnnotation(value.value)
                if obj_type in self.classVariables and value.attr in self.classVariables[obj_type]:
                    return self.classVariables[obj_type][value.attr]

            var_type = self.variables.get(value.attr)
            if var_type is not None:
                return var_type

            return self.raiseOrAuto(value)
        elif isinstance(value, ast.List):
            self.translation.imports.add("vector")
            if len(value.elts) == 0:
                return "vector<auto>"
            firstType = self.createTypeAnnotation(value.elts[0])
            for elt in value.elts[1:]:
                if self.createTypeAnnotation(elt) != firstType:
                    return "vector<auto>"
            return "vector<" + firstType + ">"

        #todo low priority
        elif isinstance(value, ast.Tuple):
            return self.raiseOrAuto(value)
        elif isinstance(value, ast.Dict):
            return self.raiseOrAuto(value)
        elif isinstance(value, ast.Set):
            return self.raiseOrAuto(value)
        elif isinstance(value, ast.Compare):
            return "bool"
        else:
            return self.raiseOrAuto(value)

    def translateExpression(self, value) -> str:
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
            return self.translateExpression(value.left) + " " + self.translateExpression(
                value.op) + " " + self.translateExpression(value.right)

        elif isinstance(value, ast.UnaryOp):
            return self.translateExpression(value.op) + self.translateExpression(value.operand)

        elif isinstance(value, ast.Compare):
            return self.translateExpression(value.left) + " " + self.translateExpression(
                value.ops[0]) + " " + self.translateExpression(value.comparators[0])

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
            #todo check is
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
                    expression = self.translateExpression(value.func.value) + "." + value.func.attr
            elif isinstance(value.func, ast.Name):
                expression = str(value.func.id)
            expression += "("
            for i in range(len(value.args)):
                arg = value.args[i]
                expression += self.translateExpression(arg)
                if i != len(value.args) - 1:
                    expression += ", "
            expression += ")"
            return expression

        elif isinstance(value, ast.Attribute):
            if isinstance(value.value, ast.Name) and value.value.id == "self":
                return "this->" + value.attr
            else:
                # Handle class variables
                return self.translateExpression(value.value) + "." + value.attr

        elif isinstance(value, ast.List):
            self.translation.imports.add("vector")
            if len(value.elts) == 0:
                return "vector<auto>()"

            expression = "{"
            for i in range(len(value.elts)):
                expression += self.translateExpression(value.elts[i])
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
        #todo low priority
        elif isinstance(value, ast.Tuple):
            self.translation.imports.add("tuple")
            return self.raiseOrAuto(value)
        elif isinstance(value, ast.Dict):
            self.translation.imports.add("map")
            return self.raiseOrAuto(value)
        elif isinstance(value, ast.Set):
            self.translation.imports.add("set")
            return self.raiseOrAuto(value)
        else:
            return self.raiseOrAuto(value)

    def assignTarget(self, target, variableType: str, isReassignment: bool) -> None:
        self.variables[target.id] = variableType
        if not isReassignment:
            self.scopedVariables[-1].append(target.id)

    def raiseOrAuto(self, node) -> str:
        if self.isDebugging:
            raise TypeError(f"Could not infer type for node '{type(node).__name__}' at line {getattr(node, 'lineno', 'unknown')}")
        return "auto"

    # @Override of functions from ast module
    def visit_Expr(self, node) -> None:
        translated_expression = self.translateExpression(node.value)
        if translated_expression:
            self.translation.emit(translated_expression + ";", "expression")

    def visit_Assign(self, node) -> None:
        variableType = self.createTypeAnnotation(node.value)
        valueString = self.translateExpression(node.value)

        # Process each target individually to support chained assignments (differ in Python and C++)
        for target in node.targets:
            if isinstance(target, ast.Name):
                isReassignment = target.id in self.variables
                self.assignTarget(target, variableType, isReassignment)

                prefix = "" if isReassignment else variableType + " "
                self.translation.emit(prefix + target.id + " = " + valueString + ";", "assignment")

            elif isinstance(target, ast.Attribute):
                # Attributes (like self.hp or player.hp)
                targetString = self.translateExpression(target)
                self.translation.emit(targetString + " = " + valueString + ";", "assignment")

            elif isinstance(target, ast.Tuple):
                # Handle tuple unpacking targets (e.g., x, y = ...)
                for element in target.elts:
                    if isinstance(element, ast.Name):
                        isReassignment = element.id in self.variables
                        self.assignTarget(element, variableType, isReassignment)

                        prefix = "" if isReassignment else variableType + " "
                        self.translation.emit(prefix + element.id + " = " + valueString + ";", "assignment")

    def visit_AugAssign(self, node) -> None:
        translation = node.target.id
        translation += " " + self.translateExpression(node.op) + "="
        translation += " " + self.translateExpression(node.value)
        self.translation.emit(translation + ";", "augment assignment")

    def enterBlock(self):
        self.scopedVariables.append([])
        self.translation.indentation += 1

    def exitBlock(self):
        for variable in self.scopedVariables[self.translation.indentation]:
            if variable in self.variables:
                self.variables.pop(variable)
        self.scopedVariables.pop()
        self.translation.indentation -= 1

    def visit_If(self, node, isElif=False) -> None:
        expression = self.translateExpression(node.test)
        keyword = "else if" if isElif else "if"

        self.translation.emit(keyword + " (" + expression + ") {", keyword)

        self.enterBlock()
        for stmt in node.body:
            self.visit(stmt)
        self.exitBlock()

        self.translation.emit("}", "endbracket - if")

        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                # Recursive elif
                self.visit_If(node.orelse[0], True)
            else:
                self.translation.emit("else {", "else")
                self.enterBlock()
                for stmt in node.orelse:
                    self.visit(stmt)
                self.exitBlock()
                self.translation.emit("}", "endbracket - else or elseif")

    def handleRange(self, args, newVariable: str) -> None:
        start = "0"
        step = 1
        if len(args) > 1:
            start = self.translateExpression(args[0])
            end = self.translateExpression(args[1])
        else:
            end = self.translateExpression(args[0])
        if len(args) > 2:
            step = self.translateExpression(args[2])
        if step == 1 or step == "1":
            stepIncrease = newVariable + "++"
        else:
            stepIncrease = newVariable + " += " + step
        self.translation.emit("for (int " + newVariable + " = " + start + ";" +
                              " " + newVariable + " < " + end + ";" +
                              " " + stepIncrease +
                              ") {", "for")

    def handleLen(self, args, newVariable: str) -> None:
        self.translation.emit("for (int " + newVariable + " = 0;" +
                              " " + newVariable + " < " + self.translateExpression(args[0]) + ";" +
                              " " + newVariable + "++) {", "for")

    def visit_For(self, node) -> None:
        newVariable = self.translateExpression(node.target)
        iterable = node.iter
        self.variables[newVariable] = self.createTypeAnnotation(node.target)

        if (isinstance(iterable, ast.Call) and
                isinstance(iterable.func, ast.Name) and
                iterable.func.id == "range"):
            self.handleRange(iterable.args, newVariable)
        elif (isinstance(iterable, ast.Call) and
              isinstance(iterable.func, ast.Name) and
              iterable.func.id == "len"):
            self.handleLen(iterable.args, newVariable)
        else:
            # I expect it to be of form "iterable<type>"
            iterableType = self.createTypeAnnotation(iterable)
            newVariableType = iterableType[iterableType.find("<") + 1:-1]
            self.translation.emit("for (" + newVariableType + " " + newVariable + " : " +
                                  self.translateExpression(iterable) + ") {", "for")

        self.enterBlock()
        for stmt in node.body:
            self.visit(stmt)
        self.exitBlock()
        self.translation.emit("}", "endbracket - for")

    def visit_Break(self, node) -> None:
        self.translation.emit("break;", "break")

    def visit_Continue(self, node) -> None:
        self.translation.emit("continue;", "continue")

    def visit_While(self, node) -> None:
        expression = self.translateExpression(node.test)
        self.translation.emit("while (" + expression + ") {", "while")
        self.enterBlock()
        for stmt in node.body:
            self.visit(stmt)
        self.exitBlock()
        self.translation.emit("}", "endbracket - while")

    def visit_FunctionDef(self, node) -> None:
        previousScope = self.translation.toMain
        self.translation.toMain = False
        className = node.name

        if node.name == "__init__" and self.translation.currentClass is not None:
            returnType = ""
            className = self.translation.currentClass
        else:
            # Handle return type
            returnType = "auto"
            if node.returns:
                if isinstance(node.returns, ast.Name):
                    returnType = node.returns.id
                    if returnType == "str":
                        returnType = "string"
                        self.translation.imports.add("string")
                elif isinstance(node.returns, ast.Constant) and node.returns.value is None:
                    returnType = "void"
            returnType += " "

        # Handle arguments
        argList = []
        for arg in node.args.args:
            if arg.arg == "self":
                continue
            argType = "auto"
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    argType = arg.annotation.id
                    if argType == "str":
                        argType = "string"
                        self.translation.imports.add("string")
                else:
                    # Shouldn't happen
                    self.raiseOrAuto(arg.annotation)
            argList.append(argType + " " + str(arg.arg))
            self.variables[arg.arg] = argType

        args = ", ".join(argList)
        self.translation.emit(returnType + className + "(" + args + ")" + " {", "function")

        self.enterBlock()

        for arg in node.args.args:
            if arg.arg != "self":
                self.scopedVariables[-1].append(str(arg.arg))

        for stmt in node.body:
            self.visit(stmt)
        self.exitBlock()

        self.translation.emit("}", "endbracket - function")
        self.translation.toMain = previousScope

    def visit_Return(self, node) -> None:
        if node.value:
            self.translation.emit("return " + self.translateExpression(node.value) + ";", "return")
        else:
            self.translation.emit("return;", "return")

    def visit_ClassDef(self, node):
        self.classes.append(node.name)
        self.classVariables[node.name] = {}
        previousScope = self.translation.toMain
        self.translation.toMain = False
        self.translation.currentClass = node.name

        self.translation.emit("class " + node.name + " {", "class")

        self.translation.emit("public:", "access modifier")
        self.enterBlock()

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
                                var_type = self.createTypeAnnotation(sub_stmt.value)
                                var_name = target.attr
                                if var_type is None:
                                    var_type = self.raiseOrAuto(sub_stmt.value)
                                self.translation.emit(var_type + " " + var_name + ";", "class variable")
                                self.classVariables[self.translation.currentClass][var_name] = var_type

        for arg in temporary_args_to_clean:
            if arg in self.variables:
                self.variables.pop(arg)

        for stmt in node.body:
            self.visit(stmt)
        self.exitBlock()

        self.translation.emit("};", "endbracket - class")

        self.translation.toMain = previousScope
        self.translation.currentClass = None

    def translate(self, text: str) -> None:
        #todo Syntax Error handling
        self.abstractSyntaxTree = ast.parse(text)
        self.visit(self.abstractSyntaxTree)
        self.translation.wrapMain()
        self.translation.finalAddImports()
        self.translation.finalCombineGlobalAndMain()

    # Debugging functions
    def printAst(self, text: str | None) -> None:
        if self.abstractSyntaxTree:
            print(self.abstractSyntaxTree)
        else:
            self.abstractSyntaxTree = ast.parse(text)
            print(ast.dump(self.abstractSyntaxTree, indent=4))

    def printCode(self) -> None:
        print(self.translation.printCode())
