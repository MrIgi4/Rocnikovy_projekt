from backend.Code import Translator

translator = Translator.Translator()
translator.translate("x = 5\ny = x + isEven(5, 7)")
translator.printCode()

if translator.cppCode.code != "int x = 5;\nint y = x + isEven(5, 7);\n":
    raise Exception("Incorrect translation")

translator = Translator.Translator()
translator.translate("x, y = 5\nz = x + y")
translator.printCode()

if translator.cppCode.code != "int x, y = 5;\nint z = x + y;\n":
    raise Exception("Incorrect translation")