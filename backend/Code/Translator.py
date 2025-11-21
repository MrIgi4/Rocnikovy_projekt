import ast

from backend.Code import Translation


class Translator(ast.NodeVisitor):
    def __init__(self):
        self.abstractSyntaxTree = None
        self.cppCode = Translation.Translation()
        self.variables = {}
        self.imports = set()

    #adds semicolon and new line character
    def addSemicolon(self):
        self.cppCode.addCodeElement(";\n", "semicolon")

    def createTypeAnnotation(self, value):
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
                return "auto"
            firstType = self.createTypeAnnotation(value.elts[0])
            for elt in value.elts[1:]:
                if self.createTypeAnnotation(elt) != firstType:
                    return "auto"
            self.imports.add("vector")
            return "vector<" + firstType + ">"

        else:
            raise TypeError(f"Unsupported node type: {type(value)}")

    def createValue(self, value):
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
            if len(value.elts) == 0:
                return "vector<auto>"

            first_type = self.createTypeAnnotation(value.elts[0])
            for elt in value.elts[1:]:
                if self.createTypeAnnotation(elt) != first_type:
                    return "std::vector<auto> "

            return "vector<" + first_type + ">"
        else:
            raise TypeError(f"Unsupported node type: {type(value)}")


    #@Override of functions from ast module
    def visit_Assign(self, node):
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

        self.cppCode.addCodeElement(translation, "assignment")
        self.addSemicolon()

    def translate(self, text):
        #todo Syntax Error handling
        self.abstractSyntaxTree = ast.parse(text)
        self.visit(self.abstractSyntaxTree)

    def printAst(self, text):
        if self.abstractSyntaxTree:
            print(self.abstractSyntaxTree)
        else:
            self.abstractSyntaxTree = ast.parse(text)
            print(ast.dump(self.abstractSyntaxTree, indent=4))

    #debbuging functions
    def printCode(self):
        print(self.cppCode.printCode())
