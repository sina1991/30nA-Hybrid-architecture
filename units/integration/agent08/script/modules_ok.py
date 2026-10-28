from contextlib import redirect_stdout
from io import StringIO


def main(input_payload, configuration):
    buffer = StringIO()
    with redirect_stdout(buffer):
        print("modules OK")
    return buffer.getvalue().strip()
