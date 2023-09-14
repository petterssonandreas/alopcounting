import dataclasses
import importlib
import sys
import json
from typing import Any
import datetime

def _dataclass_object_dump(ob):
    if isinstance(ob, datetime.date):
        return {'date': ob.isoformat(), '__dataclass__': 'datetime.date'}
    datacls = type(ob)
    if not dataclasses.is_dataclass(datacls):
        raise TypeError(f"Expected dataclass instance, got '{datacls!r}' object")
    mod = sys.modules.get(datacls.__module__)
    if mod is None or not hasattr(mod, datacls.__qualname__):
        raise ValueError(f"Can't resolve '{datacls!r}' reference")
    ref = f"{datacls.__module__}.{datacls.__qualname__}"
    fields = (f.name for f in dataclasses.fields(ob))
    return {**{f: getattr(ob, f) for f in fields}, '__dataclass__': ref}

def _dataclass_object_load(d):
    ref = d.pop('__dataclass__', None)
    if ref is None:
        return d
    if ref == 'datetime.date':
        return datetime.date.fromisoformat(d['date'])
    try:
        modname, hasdot, qualname = ref.rpartition('.')
        module = importlib.import_module(modname)
        datacls = getattr(module, qualname)
        if not dataclasses.is_dataclass(datacls) or not isinstance(datacls, type):
            raise ValueError
        return datacls(**d)
    except (ModuleNotFoundError, ValueError, AttributeError, TypeError):
        raise ValueError(f"Invalid dataclass reference {ref!r}") from None

def dataclass_json_dumps(obj: Any, indent = 0) -> str:
    return json.dumps(obj, default=_dataclass_object_dump, indent=indent)

def dataclass_json_loads(obj: str) -> Any:
    return json.loads(obj, object_hook=_dataclass_object_load)
