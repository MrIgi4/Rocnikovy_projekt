from backend.Code import Translator

def test_assign_with_function():
    translator = Translator.Translator(True)
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
    translator = Translator.Translator(True)
    translator.translate(
        "x, y = 5\n"
        "z = x + y\n"
    )

    assert translator.translation.getCode() == (
        "int main() {\n"
        "    int x = 5;\n"
        "    int y = 5;\n"
        "    int z = x + y;\n"
        "}\n"
    )

def test_assign_multiple_times():
    translator = Translator.Translator(True)
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
    translator = Translator.Translator(True)
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
    translator = Translator.Translator(True)
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
    translator = Translator.Translator(True)
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
    translator = Translator.Translator(True)
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

def test_class_def():
    translator = Translator.Translator(True)
    translator.translate(
        "class Player:\n"
        "    def __init__(self, name: str, hp: int):\n"
        "        self.name = name\n"
        "        self.hp = hp\n"
        "    def takeDamage(self, amount: int):\n"
        "        self.hp = self.hp - amount\n"
        "    def getHp(self):\n"
        "        return self.hp"
    )

    assert translator.translation.getCode() == (
         '#include <string>\n'
         '\n'
         'using namespace std;\n'
         '\n'
         'class Player {\n'
         'public:\n'
         '    string name;\n'
         '    int hp;\n'
         '    Player(string name, int hp) {\n'
         '        this->name = name;\n'
         '        this->hp = hp;\n'
         '    }\n'
         '    auto takeDamage(int amount) {\n'
         '        this->hp = this->hp - amount;\n'
         '    }\n'
         '    auto getHp() {\n'
         '        return this->hp;\n'
         '    }\n'
         '};\n'
         '\n'
         'int main() {\n'
         '}\n'
    )

def test_scope_and_state_resets():
    translator = Translator.Translator(True)
    translator.translate(
        "class Enemy:\n"
        "    def __init__(self, damage: int):\n"
        "        self.damage = damage\n"
        "class Weapon:\n"
        "    def __init__(self, damage: int):\n"
        "        self.damage = damage"
    )

    assert translator.translation.getCode() == (
        "class Enemy {\n"
        "public:\n"
        "    int damage;\n"
        "    Enemy(int damage) {\n"
        "        this->damage = damage;\n"
        "    }\n"
        "};\n"
        "class Weapon {\n"
        "public:\n"
        "    int damage;\n"
        "    Weapon(int damage) {\n"
        "        this->damage = damage;\n"
        "    }\n"
        "};\n"
        "\n"
        "int main() {\n"
        "}\n"
    )

def test_globals_and_empty_returns():
    translator = Translator.Translator(True)
    translator.translate(
        "def __init__(global_var: int):\n"
        "    return\n"
        "class App:\n"
        "    def __init__(self, version: int):\n"
        "        self.version = version\n"
        "    def crash(self):\n"
        "        return"
    )
    assert translator.translation.getCode() == (
        "auto __init__(int global_var) {\n"
        "    return;\n"
        "}\n"
        "class App {\n"
        "public:\n"
        "    int version;\n"
        "    App(int version) {\n"
        "        this->version = version;\n"
        "    }\n"
        "    auto crash() {\n"
        "        return;\n"
        "    }\n"
        "};\n"
        "\n"
        "int main() {\n"
        "}\n"
    )

def test_object_instantiation():
    translator = Translator.Translator(True)
    translator.translate(
        "class Player:\n"
        "    def __init__(self, name: str, hp: int):\n"
        "        self.name = name\n"
        "        self.hp = hp\n"
        "    def takeDamage(self, amount: int):\n"
        "        self.hp = self.hp - amount\n"
        "my_player = Player(\"Hero\", 100)\n"
        "my_player.takeDamage(10)\n"
        "current_hp = my_player.hp"
    )

    assert translator.translation.getCode() == (
        "#include <string>\n"
        "\n"
        "using namespace std;\n"
        "\n"
        "class Player {\n"
        "public:\n"
        "    string name;\n"
        "    int hp;\n"
        "    Player(string name, int hp) {\n"
        "        this->name = name;\n"
        "        this->hp = hp;\n"
        "    }\n"
        "    auto takeDamage(int amount) {\n"
        "        this->hp = this->hp - amount;\n"
        "    }\n"
        "};\n"
        "\n"
        "int main() {\n"
        "    Player my_player = Player(\"Hero\", 100);\n"
        "    my_player.takeDamage(10);\n"
        "    int current_hp = my_player.hp;\n"
        "}\n"
    )


def test_function_parameter_isolation():
    translator = Translator.Translator(True)
    translator.translate(
        "def calculate(value: int):\n"
        "    return value\n"
        "value = \"Now a string constant\""
    )

    assert "string value = " in translator.translation.getCode()

def test_consecutive_loops_scope():
    translator = Translator.Translator(True)
    translator.translate(
        "for i in range(5):\n"
        "    x = 10\n"
        "for j in range(5):\n"
        "    y = \"test\""
    )

    code = translator.translation.getCode()
    assert "int x = 10;" in code
    assert "string y = \"test\";" in code


def test_string_literal_type_deduction():
    translator = Translator.Translator(True)
    translator.translate(
        "message = \"Hello World\""
    )

    assert "string message = \"Hello World\";" in translator.translation.getCode()