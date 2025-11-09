import ast

import Translation

class Translator(ast.NodeVisitor):
    def __init__(self):
        self.abstractSyntaxTree = None
        self.cppCode = Translation.Translation()
        self.variables = {}

    #@Override of functions from ast module
    def visit_Assign(self, node):

        #add type annotation
        translation = ""
        if isinstance(node.value, ast.Name):
            #todo add logic for syntax error
            #todo or check how ast handles syntax errors
            translation = self.variables.get(node.value.id)
        elif isinstance(node.value, ast.Constant):
            string = str(type(node.value.value))
            #remove irrelevant part of string
            translation = string[8:len(string) - 2] + ' '
        else:
            raise TypeError(f"Unsupported node type: {type(node.value)}")

        #add variable names
        names = []
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.append(target.id)
                if isinstance(node.value, ast.Name):
                    self.variables[target.id] = self.variables.get(node.value.id)
                elif isinstance(node.value, ast.Constant):
                    string = str(type(node.value.value))
                    self.variables[target.id] = string[8:len(string) - 2] + ' '
        translation += ', '.join(names) + " = "

        #add value to set to
        if isinstance(node.value, ast.Name):
            translation += node.value.id
        elif isinstance(node.value, ast.Constant):
            translation += str(node.value.value)

        self.cppCode.addCodeLine(translation)


    def translate(self, text):
        self.abstractSyntaxTree = ast.parse(text)
        self.visit(self.abstractSyntaxTree)


    #debbuging functions
    def printCode(self):
        print(self.cppCode.printCode())

    def printAst(self):
        print(ast.dump(self.abstractSyntaxTree, indent=4))

translator = Translator()
translator.translate("x = 5\ny = x")
translator.printCode()