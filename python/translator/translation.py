from translator import code_element


class Translation:
    def __init__(self):
        self.indentation = 0
        self.main_elements = []
        self.global_elements = []
        self.final_code_elements = []
        self.to_main = True
        self.current_class = None
        self.imports = set()

    def emit(self, code: str, code_type: str) -> None:
        # The translator will be responsible for emitting indentation and newlines
        elem = code_element.CodeElement(code, code_type)

        if self.to_main:
            self.main_elements.append(elem)
        else:
            self.global_elements.append(elem)

    def wrap_main(self) -> None:
        wrapped = [code_element.CodeElement("int main() {\n", "main")]

        for element in self.main_elements:
            wrapped.append(element)

        wrapped.append(code_element.CodeElement("}\n", "endbracket - main"))
        self.main_elements = wrapped

    def final_add_imports(self):
        for element in self.imports:
            self.final_code_elements.append(code_element.CodeElement("#include <" + element + ">\n", "import"))
        if len(self.imports) > 0:
            self.final_code_elements.append(code_element.CodeElement("\n", "separating line"))
            self.final_code_elements.append(code_element.CodeElement("using namespace std;\n", "namespace"))
            self.final_code_elements.append(code_element.CodeElement("\n", "separating line"))

    def final_combine_global_and_main(self):
        for element in self.global_elements:
            self.final_code_elements.append(element)
        if len(self.global_elements) > 0:
            self.final_code_elements.append(code_element.CodeElement("\n", "separating line"))
        for element in self.main_elements:
            self.final_code_elements.append(element)

    def get_payload(self) -> dict:
        """Stitches the final code together and calculates precise character bounds for Java."""
        final_string = ""
        hover_map = []
        current_index = 0

        ignored_tags = {"", "separating line", "newline", "space", "assignment operator"}

        for elem in self.final_code_elements:
            length = len(elem.code)

            if elem.code_type and elem.code_type not in ignored_tags:
                hover_map.append({
                    "start": current_index,
                    "end": current_index + length,
                    "tag": elem.code_type
                })

            final_string += elem.code
            current_index += length

        return {
            "cpp_code": final_string,
            "hover_map": hover_map
        }

    def print_code(self) -> None:
        print("".join(elem.code for elem in self.final_code_elements))

    def get_code(self) -> str:
        return "".join(elem.code for elem in self.final_code_elements)