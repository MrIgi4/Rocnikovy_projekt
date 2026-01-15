from backend.Code import CodeElement


class Translation:
    def __init__(self):
        self.code = ""
        self.codeLines = []
        self.codeElements = []

    #todo create CodeType class or find out that it's unnecessary
    def addCodeElement(self, code: str, codeType: str) -> None:
        self.code += code
        self.codeElements.append(CodeElement.CodeElement(code, codeType))

    def printCode(self) -> None:
        print(self.code)