from collections.abc import Collection
import abc
import importlib.resources
import typing

from hat import aio
from hat import json


with importlib.resources.as_file(importlib.resources.files(__package__) /
                                 'json_schema_repo.json') as _path:
    json_schema_repo: json.SchemaRepository = json.SchemaRepository(
        json.json_schema_repo,
        json.SchemaRepository.from_json(_path))
    """JSON schema repository"""

TriggerType: typing.TypeAlias = str
"""Trigger type (segments are delimited by '/')"""

TriggerName: typing.TypeAlias = str
"""Trigger name (segments are delimited by '/')"""

FunctionName: typing.TypeAlias = str
"""Function name (segments are delimited by '.')"""

UnitName: typing.TypeAlias = str
"""Unit name"""

ActionName: typing.TypeAlias = str
"""Action name"""


class Trigger(typing.NamedTuple):
    """Trigger"""
    type: TriggerType
    name: TriggerName
    data: json.Data


class Unit(aio.Resource):
    """Unit"""

    @abc.abstractmethod
    async def call(self,
                   function: FunctionName,
                   args: Collection[json.Data],
                   trigger: Trigger | None
                   ) -> json.Data:
        """Evaluate function call

        Multiple calls to this method can occur concurrently.

        This method can be coroutine or regular function.

        """


UnitConf: typing.TypeAlias = json.Data
"""Unit configuration"""

RaiseTriggerCb: typing.TypeAlias = aio.AsyncCallable[[Trigger], None]
"""Raise trigger callback"""

CreateUnit: typing.TypeAlias = aio.AsyncCallable[[UnitConf,
                                                  RaiseTriggerCb | None],
                                                 Unit]
"""Create unit callback"""


class UnitInfo(typing.NamedTuple):
    """Unit info

    Unit is implemented as python module which is dynamically imported.
    It is expected that this module contains `info` which is instance of
    `UnitInfo`.

    If unit defines JSON schema repository and JSON schema id, JSON schema
    repository will be used for additional validation of unit configuration
    with JSON schema id.

    """
    name: UnitName
    functions: set[FunctionName]
    create: CreateUnit
    json_schema_id: str | None = None
    json_schema_repo: json.SchemaRepository | None = None


def import_unit_info(py_module_str: str) -> UnitInfo:
    """Import unit info"""
    py_module = importlib.import_module(py_module_str)
    info = py_module.info

    if not isinstance(info, UnitInfo):
        raise Exception('invalid unit implementation')

    return info
