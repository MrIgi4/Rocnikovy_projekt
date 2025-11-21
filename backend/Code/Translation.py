from backend.Code import CodeElement


class Translation:
    def __init__(self):
        self.code = ""
        self.codeLines = []
        self.codeElements = []

    def addCodeElement(self, code, codeType):
        self.code += code
        self.codeElements.append(CodeElement.CodeElement(code, codeType))

    def printCode(self):
        print(self.code)