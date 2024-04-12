from hat import duktape

from hat.controller.interpreters import common


class Duktape(common.Interpreter):

    def __init__(self, action_codes, infos, call_cb):
        self._interpreter = _create_interpreter(infos, call_cb)
        self._actions = {
            action: self._interpreter.eval(common.create_js_action_code(code))
            for action, code in action_codes.items()}

    def eval_code(self, code):
        self._interpreter.eval(code)

    def eval_action(self, action):
        self._actions[action]()


def _create_interpreter(infos, call_cb):
    api_code = common.create_js_api_code(infos)

    interpreter = duktape.Interpreter()
    api_fn = interpreter.eval(api_code)
    api_fn(call_cb)

    return interpreter
