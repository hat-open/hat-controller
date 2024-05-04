from hat.controller.interpreters import _quickjs
from hat.controller.interpreters import common


class QuickJS(common.JsInterpreter):

    def __init__(self):
        self._interpreter = _quickjs.Interpreter()

    def eval(self, code: str) -> common.JsData:
        return self._interpreter.eval(code)
