from hat.controller.common import *  # NOQA

from collections.abc import Iterable

from hat import json

from hat.controller.common import UnitInfo


def create_js_api_code(infos: Iterable[UnitInfo]) -> str:
    api_dict = _create_js_api(infos)
    units = _encode_js_api(api_dict)

    return f"var units; (function(f) {{ units = {units}; }})"


def create_js_action_code(code: str) -> str:
    return f"new Function({json.encode(code)})"


def _create_js_api(infos):
    api_dict = {}
    for info in infos:
        unit_api_dict = {}

        for function in info.functions:
            segments = function.split('.')
            parent = unit_api_dict

            for segment in segments[:-1]:
                if segment not in parent:
                    parent[segment] = {}

                parent = parent[segment]

            parent[segments[-1]] = (f"function() {{ return f("
                                    f"'{info.name}', "
                                    f"'{function}', "
                                    f"Array.prototype.slice.call(arguments)"
                                    f"); }}")

        api_dict[info.name] = unit_api_dict

    return api_dict


def _encode_js_api(x):
    if isinstance(x, str):
        return x

    elements = (f"'{k}': {_encode_js_api(v)}" for k, v in x.items())
    return f"{{{', '.join(elements)}}}"
