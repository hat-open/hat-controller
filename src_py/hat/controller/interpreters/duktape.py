from hat.controller.interpreters import _duktape
from hat.controller.interpreters import common


class Duktape(common.JsInterpreter):

    def __init__(self):
        self._interpreter = _duktape.Interpreter()

    def eval(self, code: str) -> common.JsData:
        return self._interpreter.eval(code)
