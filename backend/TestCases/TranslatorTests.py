from backend.Code import Translator

def test_assign_with_function():
    translator = Translator.Translator()
    translator.translate(
        "x = 5\n"
        "y = x + isEven(5, 7)\n"
    )

    assert translator.translation.getCode() == (
        "int main() {\n"
        "    int x = 5;\n"
        "    int y = x + isEven(5, 7);\n"
        "}\n"
    )

def test_assign_multiple_variables():
    translator = Translator.Translator()
    translator.translate(
        "x, y = 5\n"
        "z = x + y\n"
    )

    assert translator.translation.getCode() == (
        "int main() {\n"
        "    int x, y = 5;\n"
        "    int z = x + y;\n"
        "}\n"
    )

def test_assign_multiple_times():
    translator = Translator.Translator()
    translator.translate(
        "x = 23\n"
        "x = x + 1\n"
    )

    assert translator.translation.getCode() == (
        "int main() {\n"
        "    int x = 23;\n"
        "    x = x + 1;\n"
        "}\n"
    )

def test_basic_if():
    translator = Translator.Translator()
    translator.translate(
        "x = 23\n"
        "if x == 23:\n"
        "    x = x + 1\n"
    )

    assert translator.translation.getCode() == (
        "int main() {\n"
        "    int x = 23;\n"
        "    if (x == 23) {\n"
        "        x = x + 1;\n"
        "    }\n"
        "}\n"
    )

def test_2_for_loops():
    translator = Translator.Translator()
    translator.translate(
        "x = 23\n"
        "y = [1, 2, 3]\n"
        "for i in range(1, x):\n"
        "    x = x + 1\n"
        "for i in y:\n"
        "    x += 1\n"
    )

    assert translator.translation.getCode() == (
        "#include <vector>\n"
        "\n"
        "using namespace std;\n"
        "\n"
        "int main() {\n"
        "    int x = 23;\n"
        "    vector<int> y = {1, 2, 3};\n"
        "    for (int i = 1; i < x; i++) {\n"
        "        x = x + 1;\n"
        "    }\n"
        "    for (int i : y) {\n"
        "        x += 1;\n"
        "    }\n"
        "}\n"
    )

def test_else_ifs():
    translator = Translator.Translator()
    translator.translate(
        "if true:\n"
        "    x = -12\n"
        "if true:\n"
        "    x = 5\n"
        "elif false:\n"
        "    x = -1\n"
        "else:\n"
        "    x = 3\n"
    )

    assert translator.translation.getCode() == (
        "int main() {\n"
        "    if (true) {\n"
        "        int x = -12;\n"
        "    }\n"
        "    if (true) {\n"
        "        int x = 5;\n"
        "    }\n"
        "    else if (false) {\n"
        "        int x = -1;\n"
        "    }\n"
        "    else {\n"
        "        int x = 3;\n"
        "    }\n"
        "}\n"
    )

def test_while():
    translator = Translator.Translator()
    translator.translate(
        "x = 0\n"
        "while(true):\n"
        "    x = x + 1\n"
    )

    assert translator.translation.getCode() == (
        "int main() {\n"
        "    int x = 0;\n"
        "    while (true) {\n"
        "        x = x + 1;\n"
        "    }\n"
        "}\n"
    )