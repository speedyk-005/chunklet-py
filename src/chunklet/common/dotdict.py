"""
DotDict/DotList with Box-compatible serialization.

This module embeds code originally from ``dotdict3`` (MIT License).
Co-authored by:
  - speedyk-005
  - Patrick Elmer <patrick@elmer.ws> (https://github.com/dotdict/dotdict3)

Modifications: added ``to_dict()``, ``to_json()``, ``to_yaml()``,
``to_msgpack()``, ``to_toml()``, ``to_csv()`` for backward compatibility
with the python-box API.
"""

import json


class DotDict(dict):
    """A dict subclass with dot-notation access and automatic nested conversion.

    Basic usage::

        >>> d = DotDict({"name": "John", "age": 30})
        >>> d.name
        'John'
        >>> d.age
        30

    Nested dicts auto-convert::

        >>> d = DotDict({"user": {"name": "Bob", "age": 25}})
        >>> d.user.name
        'Bob'
        >>> d.user.age
        25

    Lists auto-convert to DotList::

        >>> d = DotDict({"users": [{"name": "Alice"}, {"name": "Bob"}]})
        >>> d.users[0].name
        'Alice'
        >>> isinstance(d.users, DotList)
        True

    Dot notation assignment::

        >>> d = DotDict()
        >>> d.name = "Alice"
        >>> d.name
        'Alice'
    """

    def __init__(self, data=None):
        if data is not None:
            for key, value in data.items():
                self[key] = value

    def __setitem__(self, key, value):
        return super().__setitem__(key, _convert(value))

    # Redirect attribute operations to dictionary methods
    __delattr__ = dict.__delitem__
    __getattr__ = dict.__getitem__
    __setattr__ = __setitem__

    def to_dict(self):
        """Recursively convert back to a plain dict.

        >>> d = DotDict({"a": {"b": 1}, "c": [{"d": 2}]})
        >>> d.to_dict()
        {'a': {'b': 1}, 'c': [{'d': 2}]}
        """
        return {k: _to_plain(v) for k, v in self.items()}

    def to_json(self, filename=None, **kwargs):
        """Serialize to a JSON string, or write to a file if *filename* is given.

        >>> DotDict({"content": "Hello", "count": 3}).to_json()
        '{"content": "Hello", "count": 3}'
        """
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, **kwargs)
        else:
            return json.dumps(self.to_dict(), ensure_ascii=False, **kwargs)

    def to_yaml(self, filename=None, default_flow_style=False, **kwargs):
        try:
            import yaml
        except ImportError:
            raise ImportError("pyyaml required: pip install pyyaml") from None
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                yaml.dump(self.to_dict(), f, default_flow_style=default_flow_style, **kwargs)
        else:
            return yaml.dump(self.to_dict(), default_flow_style=default_flow_style, **kwargs)

    def to_toml(self, filename=None):
        try:
            import toml
        except ImportError:
            raise ImportError("toml required: pip install toml") from None
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                toml.dump(self.to_dict(), f)
        else:
            return toml.dumps(self.to_dict())

    def to_msgpack(self, filename=None, **kwargs):
        """Serialize to MessagePack bytes, or write to a file if *filename* is given.

        >>> import msgpack
        >>> d = DotDict({"a": 1, "b": [2, 3]})
        >>> msgpack.unpackb(d.to_msgpack())
        {'a': 1, 'b': [2, 3]}
        """
        try:
            import msgpack
        except ImportError:
            raise ImportError("msgpack required: pip install msgpack") from None
        if filename:
            with open(filename, "wb") as f:
                msgpack.pack(self.to_dict(), f, **kwargs)
        else:
            return msgpack.packb(self.to_dict(), **kwargs)


class DotList(list):
    """A list subclass with automatic nested dict/list conversion.

    >>> l = DotList([{"a": 1}, {"b": 2}])
    >>> l[0].a
    1
    >>> l[1].b
    2
    """

    def __init__(self, items=None):
        if items is not None:
            for item in items:
                self.append(item)

    def append(self, items):
        return super().append(_convert(items))

    def insert(self, index, items):
        return super().insert(index, _convert(items))

    def to_dict(self):
        """Recursively convert back to a plain list.

        >>> DotList([DotDict({"a": 1}), DotDict({"b": 2})]).to_dict()
        [{'a': 1}, {'b': 2}]
        """
        return [_to_plain(v) for v in self]


def _convert(obj):
    """Recursively converts dicts/lists to DotDict/DotList if not already converted."""
    if isinstance(obj, dict) and not isinstance(obj, DotDict):
        return DotDict(obj)
    if isinstance(obj, list) and not isinstance(obj, DotList):
        return DotList(obj)
    return obj


def _to_plain(obj):
    """Recursively converts DotDict/DotList back to plain dict/list."""
    if isinstance(obj, DotDict):
        return {k: _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (DotList, tuple)):
        return [_to_plain(v) for v in obj]
    return obj
