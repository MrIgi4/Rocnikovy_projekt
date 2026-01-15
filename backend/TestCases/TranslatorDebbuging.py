from backend.Code import Translator

#temporary debugging file
pythonCode = "x = []"

translator = Translator.Translator()
translator.printAst(pythonCode)
translator.translate(pythonCode)
translator.printCode()