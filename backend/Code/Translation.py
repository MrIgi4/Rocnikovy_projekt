from backend.Code import CodeElement


class Translation:
    def __init__(self):
        self.indentation = 0
        self.mainElements = []
        self.globalElements = []
        self.finalCodeElements = []
        self.toMain = True
        self.currentClass = None
        self.imports = set()

    #todo create CodeType class or find out that it's unnecessary

    def emit(self, code: str, codeType: str) -> None:
        # todo - inaccurate - makes entire line an assignment even if it contains e.g. calls
        line = "    " * self.indentation + code + "\n"
        elem = CodeElement.CodeElement(line, codeType)

        if self.toMain:
            self.mainElements.append(elem)
        else:
            self.globalElements.append(elem)

    def wrapMain(self) -> None:
        wrapped = [CodeElement.CodeElement("int main() {\n", "main")]

        for element in self.mainElements:
            wrapped.append(CodeElement.CodeElement("    " + element.code, element.codeType))

        wrapped.append(CodeElement.CodeElement("}\n", "endbracket - main"))
        self.mainElements = wrapped

    def finalAddImports(self):
        for element in self.imports:
            self.finalCodeElements.append(CodeElement.CodeElement("#include <" + element + ">\n", "import"))
        if len(self.imports) > 0:
            self.finalCodeElements.append(CodeElement.CodeElement("\n", "separating line"))
            self.finalCodeElements.append(CodeElement.CodeElement("using namespace std;\n", "namespace"))
            self.finalCodeElements.append(CodeElement.CodeElement("\n", "separating line"))

    def finalCombineGlobalAndMain(self):
        for element in self.globalElements:
            self.finalCodeElements.append(element)
        if len(self.globalElements) > 0:
            self.finalCodeElements.append(CodeElement.CodeElement("\n", "separating line"))
        for element in self.mainElements:
            self.finalCodeElements.append(element)

    def printCode(self) -> None:
        print("".join(elem.code for elem in self.finalCodeElements))

    def getCode(self) -> str:
        return "".join(elem.code for elem in self.finalCodeElements)