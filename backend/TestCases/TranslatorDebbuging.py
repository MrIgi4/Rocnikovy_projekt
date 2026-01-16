from backend.Code import Translator

#temporary debugging file
pythonCode = ("x = 23\n"
              "if x == 23:\n"
              "    x = x + 1\n"
              "print(func(x))\n")

translator = Translator.Translator()
translator.printAst(pythonCode)
translator.translate(pythonCode)
translator.printCode()