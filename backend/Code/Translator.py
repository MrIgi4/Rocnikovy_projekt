import ast

from backend.Code import Translation


class Translator(ast.NodeVisitor):
    """Translates Python code to c++ code."""
    def __init__(self):
        self.abstractSyntaxTree = None
        self.cppCode = Translation.Translation()
        self.variables = {}
        self.scopedVariables: list[list[str]] = [] #list of variables by indentation for deletion after their scope is exited
        self.imports = set()
        self.indentation = 0

    def addSemicolon(self):
        """Adds semicolon and new line character."""
        self.cppCode.addCodeElement(";\n", "semicolon")

    def createTypeAnnotation(self, value) -> str:
        """Creates and returns type annotation for assignment of variables, e.g. int."""
        if isinstance(value, ast.Name):
            return self.variables.get(value.id)
        elif isinstance(value, ast.Constant):
            string = str(type(value.value))
            return string[8:len(string) - 2]  # remove irrelevant part of type annotation
        elif isinstance(value, ast.BinOp):
            return self.createTypeAnnotation(value.left)
        elif isinstance(value, ast.UnaryOp):
            return self.createTypeAnnotation(value.operand)
        elif isinstance(value, ast.Call):
            return "auto"
        elif isinstance(value, ast.List):
            if len(value.elts) == 0:
                return "vector<auto>"
            firstType = self.createTypeAnnotation(value.elts[0])
            for elt in value.elts[1:]:
                if self.createTypeAnnotation(elt) != firstType:
                    return "vector<auto>"
            return "vector<" + firstType + ">"
        #todo low priority
        elif isinstance(value, ast.Tuple):
            return None
        elif isinstance(value, ast.Dict):
            return None
        elif isinstance(value, ast.Set):
            return None
        elif isinstance(value, ast.Compare):
            return "bool"
        else:
            raise TypeError(f"Unsupported node type: {type(value)}")

    def createValue(self, value) -> str:
        """Evaluates an expression, translates it into c++ and returns it."""
        if isinstance(value, ast.Name):
            return value.id
        elif isinstance(value, ast.Constant):
            return str(value.value)
        elif isinstance(value, ast.BinOp):
            return self.createValue(value.left) + " " + self.createValue(value.op) + " " + self.createValue(value.right)
        elif isinstance(value, ast.UnaryOp):
            return self.createValue(value.op) + self.createValue(value.operand)
        elif isinstance(value, ast.Compare):
            return self.createValue(value.left) + " " + self.createValue(value.ops[0]) + " " + self.createValue(value.comparators[0])
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
                expression = str(value.func.value) + "." + value.func.attr
            elif isinstance(value.func, ast.Name):
                expression = str(value.func.id)
            expression += "("
            for i in range(len(value.args)):
                arg = value.args[i]
                expression += self.createValue(arg)
                if i != len(value.args) - 1:
                    expression += ", "
            expression += ")"
            return expression
        elif isinstance(value, ast.List):
            self.imports.add("vector")
            if len(value.elts) == 0:
                return "vector<auto>()"

            first_type = self.createTypeAnnotation(value.elts[0])
            for elt in value.elts[1:]:
                if self.createTypeAnnotation(elt) != first_type:
                    return "vector<auto>()"

            return "vector<" + first_type + ">()"
        #todo low priority
        elif isinstance(value, ast.Tuple):
            self.imports.add("tuple")
            return None
        elif isinstance(value, ast.Dict):
            self.imports.add("map")
            return None
        elif isinstance(value, ast.Set):
            self.imports.add("set")
            return None
        else:
            raise TypeError(f"Unsupported node type: {type(value)}")

    def emitCode(self, code: str, codeType: str) -> None:
        #todo - inaccurate - makes entire line an assignment even if it contains e.g. calls
        self.cppCode.addCodeElement("    " * self.indentation + code, codeType)

    def assignTarget(self, target, variableType: str, isReassignment: bool) -> None:
        self.variables[target.id] = variableType
        if len(self.scopedVariables) <= self.indentation:
            self.scopedVariables.append([])
        if not isReassignment:
            self.scopedVariables[self.indentation].append(target.id)

    #@Override of functions from ast module
    def visit_Assign(self, node) -> None:
        variableType = self.createTypeAnnotation(node.value)

        if isinstance(node.targets[0], ast.Name):
            isReassignment = self.variables.keys().__contains__(node.targets[0].id)
        else:
            isReassignment = False

        if isReassignment:
            translation = ""
        else:
            translation = variableType + ' '

        names = []
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.append(target.id)
                self.assignTarget(target, variableType, isReassignment)
            elif isinstance(target, ast.Tuple):
                for element in target.elts:
                    if isinstance(element, ast.Name):
                        names.append(element.id)
                        self.assignTarget(element, variableType, isReassignment)

        variables = ""
        for i in range(len(names)):
            variables += names[i]
            if i != len(names) - 1:
                variables += ", "

        translation += variables + " = "
        translation += self.createValue(node.value)

        self.emitCode(translation, "assignment")
        self.addSemicolon()

    def visit_AugAssign(self, node) -> None:
        translation = node.target.id
        translation += " " + self.createValue(node.op) + "="
        translation += " " + self.createValue(node.value)
        self.emitCode(translation, "augment assignment")
        self.addSemicolon()

    def enterBlock(self):
        if len(self.scopedVariables) <= self.indentation:
            self.scopedVariables.append([])
        self.indentation += 1

    def exitBlock(self):
        for variable in self.scopedVariables[self.indentation]:
            self.variables.pop(variable)
        self.scopedVariables.pop(self.indentation - 1)
        self.indentation -= 1

    def visit_If(self, node) -> None:
        expression = self.createValue(node.test)
        self.emitCode("if (" + expression + ") {\n", "if")
        self.enterBlock()
        for stmt in node.body:
            self.visit(stmt)
        self.exitBlock()
        self.emitCode("}\n", "endbracket - if")

        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                self.emitCode("else ", "elseif")
                self.visit_If(node.orelse[0])  # recursive elif
            else:
                self.emitCode("else {\n", "else")
                self.enterBlock()
                for stmt in node.orelse:
                    self.visit(stmt)
                self.exitBlock()
                self.emitCode("}\n", "endbracket - else or elseif")

    def handleRange(self, args, newVariable : str) -> None:
        start = 0
        step = 1
        if len(args) > 1:
            start = self.createValue(args[0])
            end = self.createValue(args[1])
        else:
            end = self.createValue(args[0])
        if len(args) > 2:
            step = self.createValue(args[2])
        if step == 1:
            stepIncrease = newVariable + "++"
        else:
            stepIncrease = newVariable + " += " + step
        self.emitCode("for (int " + newVariable + " = " + start + ";" +
                      " " + newVariable + " < " + end + ";" +
                      " " + stepIncrease +
                      ") {\n", "for")

    def handleLen(self, args, newVariable : str) -> None:
        self.emitCode("for (int " + newVariable + " = 0;" +
                      " " + newVariable + " < " + self.createValue(args[0]) + ";" +
                      " " + newVariable + "++) {\n", "for")

    def visit_For(self, node) -> None:
        newVariable = self.createValue(node.target)
        iterable = node.iter
        self.variables[newVariable] = self.createTypeAnnotation(node.target)
        self.scopedVariables.append([])

        if (isinstance(iterable, ast.Call) and
              isinstance(iterable.func, ast.Name) and
              iterable.func.id == "range"):
            self.handleRange(iterable.args, newVariable)
        elif (isinstance(iterable, ast.Call) and
              isinstance(iterable.func, ast.Name) and
              iterable.func.id == "len"):
            self.handleLen(iterable.args, newVariable)
        else:
            #I expect it to be of form "iterable<type>"
            iterableType = self.createTypeAnnotation(iterable)
            newVariableType = iterableType[iterableType.find("<") + 1:-1]
            self.emitCode("for (" + newVariableType + " " + newVariable + " : " +
                          self.createValue(iterable) + ") {\n", "for")

        self.enterBlock()
        for stmt in node.body:
            self.visit(stmt)
        self.exitBlock()
        self.emitCode("}\n", "endbracket - for")

    def visit_While(self, node) -> None:
        expression = self.createValue(node.test)
        self.emitCode("while (" + expression + ") {\n", "while")
        self.enterBlock()
        for stmt in node.body:
            self.visit(stmt)
        self.exitBlock()
        self.emitCode("}\n", "endbracket - while")

    def translate(self, text: str) -> None:
        #todo Syntax Error handling
        self.abstractSyntaxTree = ast.parse(text)
        self.visit(self.abstractSyntaxTree)

    #debbuging functions
    def printAst(self, text: str | None) -> None:
        if self.abstractSyntaxTree:
            print(self.abstractSyntaxTree)
        else:
            self.abstractSyntaxTree = ast.parse(text)
            print(ast.dump(self.abstractSyntaxTree, indent=4))

    def printCode(self) -> None:
        print(self.cppCode.printCode())
