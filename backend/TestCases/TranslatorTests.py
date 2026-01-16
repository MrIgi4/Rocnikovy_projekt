from backend.Code import Translator

def test_assign_with_function():
    translator = Translator.Translator()
    translator.translate("x = 5\n"
                         "y = x + isEven(5, 7)\n")
    translator.printCode()

    assert translator.cppCode.code == ("int x = 5;\n"
                                       "int y = x + isEven(5, 7);\n")

def test_assign_multiple_variables():
    translator = Translator.Translator()
    translator.translate("x, y = 5\n"
                         "z = x + y")
    translator.printCode()

    assert translator.cppCode.code == ("int x, y = 5;\n"
                                       "int z = x + y;\n")

def test_assign_multiple_times():
    translator = Translator.Translator()
    translator.translate("x = 23\n"
                         "x = x + 1")
    translator.printCode()

    assert translator.cppCode.code == ("int x = 23;\n"
                                       "x = x + 1;\n")

def test_basic_if():
    translator = Translator.Translator()
    translator.translate("x = 23\n"
                         "if x == 23:\n"
                         "    x = x + 1\n")
    translator.printCode()

    assert translator.cppCode.code == ("int x = 23;\n"
                                       "if (x == 23) {\n"
                                       "    x = x + 1;\n"
                                       "}\n")