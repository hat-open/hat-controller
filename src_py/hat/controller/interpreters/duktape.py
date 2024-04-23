from hat.controller.interpreters import _duktape
from hat.controller.interpreters import common


class Duktape(common.Interpreter):

    def __init__(self):
        self._interpreter = _duktape.Interpreter()

    def eval(self, code):
        return self._interpreter.eval(code)
