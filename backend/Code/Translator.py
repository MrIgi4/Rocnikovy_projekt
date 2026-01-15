import ast

from backend.Code import Translation


class Translator(ast.NodeVisitor):
    """Translates Python code to c++ code."""
    def __init__(self):
        self.abstractSyntaxTree = None
        self.cppCode = Translation.Translation()
        self.variables = {}
        self.imports = set()

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
        elif isinstance(value, ast.Add):
            return "+"
        elif isinstance(value, ast.Sub):
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
                return "vector<auto>"

            first_type = self.createTypeAnnotation(value.elts[0])
            for elt in value.elts[1:]:
                if self.createTypeAnnotation(elt) != first_type:
                    return "vector<auto>"

            return "vector<" + first_type + ">"
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

    #@Override of functions from ast module
    def visit_Assign(self, node) -> None:
        variableType = self.createTypeAnnotation(node.value)

        names = []
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.append(target.id)
                self.variables[target.id] = variableType
            elif isinstance(target, ast.Tuple):
                for element in target.elts:
                    if isinstance(element, ast.Name):
                        names.append(element.id)
                        self.variables[element.id] = variableType

        translation = variableType + ' '
        for i in range(len(names)):
            translation += names[i]
            if i != len(names) - 1:
                translation += ", "
        translation += " = "

        translation += self.createValue(node.value)

        #todo inaccurate - makes entire line an assignment even if it contains e.g. calls
        self.cppCode.addCodeElement(translation, "assignment")
        self.addSemicolon()

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
