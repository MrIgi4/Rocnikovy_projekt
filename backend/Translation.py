class Translation:
    def __init__(self):
        self.code = ""
        self.codeLines = []

    def addCodeLine(self, codeLine):
        self.code += "\n"
        self.code += codeLine
        self.codeLines.append(codeLine)

    def printCode(self):
        print(self.code)