from backend.Code import Translator

def test_assign_with_function():
    translator = Translator.Translator()
    translator.translate("x = 5\ny = x + isEven(5, 7)")
    translator.printCode()

    assert translator.cppCode.code == "int x = 5;\nint y = x + isEven(5, 7);\n"

def test_assign_multiple_variables():
    translator = Translator.Translator()
    translator.translate("x, y = 5\nz = x + y")
    translator.printCode()

    assert translator.cppCode.code == "int x, y = 5;\nint z = x + y;\n"
