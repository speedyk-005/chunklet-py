"""
DotDict/DotList: dict and list subclasses with dot-notation access.

This module embeds code originally from ``dotdict3`` (MIT License).
Co-authored by:
  - speedyk-005
  - Patrick Elmer <patrick@elmer.ws> (https://github.com/dotdict/dotdict3)
"""


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

    def to_std_dict(self):
        """Recursively convert back to plain ``dict``/``list`` containers.

        ``DotDict`` is itself a ``dict``, so this is not needed for equality or
        for ``json``. It is needed when a consumer requires exact standard
        types, e.g. ``yaml.dump`` emits ``!!python/object`` tags for dict
        subclasses.

        >>> d = DotDict({"a": {"b": 1}, "c": [{"d": 2}]})
        >>> d.to_std_dict()
        {'a': {'b': 1}, 'c': [{'d': 2}]}
        """
        return {k: _to_plain(v) for k, v in self.items()}


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

    def to_std_dict(self):
        """Recursively convert back to plain ``list`` containers.

        >>> DotList([DotDict({"a": 1}), DotDict({"b": 2})]).to_std_dict()
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
