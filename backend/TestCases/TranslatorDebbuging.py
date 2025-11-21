from backend.Code import Translator

pythonCode = "x = []"

translator = Translator.Translator()
translator.printAst(pythonCode)
translator.translate(pythonCode)
translator.printCode()