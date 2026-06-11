import json
import sys

from translator.translator import Translator

if __name__ == "__main__":
    # Ensure Java passed the temporary file path argument
    if len(sys.argv) < 2:
        print("// Error: No input file provided to Python backend.")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        # Read the code Java sent over
        with open(file_path, "r", encoding="utf-8") as f:
            python_source_code = f.read()

        translator = Translator()
        translator.translate(python_source_code)

        cpp_output = translator.translation.getCode()

        # Example documentation
        # todo add actual documentation
        documentation_list = [
            {"start": 0, "end": 3, "doc": "documentation for first 3 characters"}
        ]

        translator_payload = {
            "cpp_code": cpp_output,
            "documentation_list": documentation_list
        }

        # Captured by Java
        print(json.dumps(translator_payload))

    except Exception as e:
        # todo add more exception cases
        import traceback

        print(f"// Python Exception occurred:\n{traceback.format_exc()}")
        sys.exit(1)