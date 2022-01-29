# rsdict

[![Python package](https://github.com/kihiyuki/python-rsdict/actions/workflows/python-package.yml/badge.svg)](https://github.com/kihiyuki/python-rsdict/actions/workflows/python-package.yml)

<!-- ref: rsdict.__doc__ -->
rsdict is a **restricted** and **resetable** dictionary,
a subclass of Python `dict` (built-in dictionary).

[README(日本語)](README_ja.md)

## Features

- Type-restrict(able): If activated, every type of value is fixed to its initial type.
- Key-restrict(able): If activated, cannot add or delete keys.
- Resettable: to initial value(s).

## Parameters

Initialize:
`rsdict(items, frozen=False, fixkey=True, fixtype=True, cast=False)`

<!-- ref: rsdict.__init__.__doc__ -->
- items (dict): Initial items.
    Built-in dictionary only. kwargs are not supported.
- frozen (bool, optional): If True, the instance will be frozen (read-only).
    Assigning to fields of frozen instance always raises AttributeError.
- fixkey: (bool, optional): If True, cannot add or delete keys.
- fixtype (bool, optional): if True, cannot change type of keys.
- cast (bool, optional): If True, cast to initial type (if possible).
    If False, allow only the same type of initial value.

## Additional methods

- `set(key, value)`: Alias of `__setitem__`.
- `to_dict() -> dict`: Convert to dict instance.
- `reset(key: Optional[Any]) -> None`: Reset value to the initial value. If key is None, reset all values.
- `is_changed() -> bool`: If True, the values are changed from initial.
- `get_initial() -> dict`: Return initial values.

## Disabled methods

<!-- ref: rsdict.__getattribute__ -->
- `fromkeys()`

## Notes

- [Tested with Python 3.6, 3.7, 3.8, 3.9, 3.10.](.github/workflows/python-package.yml)
- Expected type of values:
    `int`, `float`, `str`, `bool`, `None`,
    `list`, `dict`, `tuple`,
    `pathlib.Path`
- Third-party object is not supported.
- `numpy.ndarray` will be corrupted if cast=True.

## Example

### Initialize

<!-- from rsdict.__init__.__doc__ -->
```python
>>> from rsdict import rsdict

>>> d = dict
...     name = "John",
...     enable = True,
...     count = 0,
... )
>>> rd = rsdict(d)
>>> rd
rsdict({'name': 'John', 'enable': True, 'count': 0},
         frozen=False, fixkey=True, fixtype=False)
```

### Get

Same as `dict`.

```python
>>> rd["count"] == d["count"]
True
>>> rd.get("count") == d["count"]
True
>>> rd.get("xyz")
None
```

### Set

```python
>>> rd["enable"] = False
>>> rd.set("enable", False)
```

```python
# If frozen, always raise an exception.
>>> rd_frozen = rsdict(dict(count=1), frozen=True)
>>> rd_frozen["count"] = 2
AttributeError
```

```python
# If fixtype and not cast, different-type value raise an exception.
>>> rd["count"] = "2"
TypeError

# If fixtype and cast, cast value to initial type.
>>> rd["count"] = "2"
>>> rd["count"]
2
>>> rd["count"] = "abc"
ValueError

# If not fixtype, anything can be set.
>>> rd["count"] = "2"
>>> rd["count"]
'2'
```

```python
# If fixkey, setting with a new key raises an exception.
>>> rd["location"] = 9
AttributeError

# If not fixkey, a new key can be set.
>>> rd["location"] = 9
>>> rd["location"]
9
```

### Delete

If frozen or fixkey, raise AttributeError.

```python
# If frozen or fixkey, deleting key raises an exception.
>>> del rd["count"]
AttributeError

# Else, delete both current and initial values.
>>> rd_keyfree = rsdict(dict(a=1, b=2, c=3), fixkey=False)
>>> del rd_keyfree["b"]
>>> rd_keyfree.keys()
dict_keys(['a', 'c'])
>>> rd_keyfree.get_initial().keys()
dict_keys(['a', 'c'])
```

### Reset

```python
# Check whether the values are changed from initial.
>>> rd.is_changed()
False
# Change some values.
>>> rd["enable"] = False
>>> rd["count"] = 5
>>> rd.is_changed()
True

# Reset by specifying key.
>>> rd.reset("count")
>>> rd["count"]
0
>>> rd.is_changed()
True

# Reset all values.
>>> rd.reset()
>>> rd.is_changed()
False
```

### Compare

```python
>>> rd1 = rsdict({"key1": 10, "key2": "abc"})
>>> rd2 = rsdict({"key1": 20, "key2": "abc"})
# Change current value.
>>> rd2["key1"] = 10

# Current values are equal.
>>> rd1 == rd2
True

# Initial values are not equal.
>>> rd1.get_initial() == rd2.get_initial()
False

# If compare with dict, use current values.
>>> d2 = rd2.to_dict()
>>> rd2 == d2
```

### Union

`Python >= 3.9`

```python
>>> rd = rsdict({"key1": 10, "key2": "abc"}, fixkey=False)
>>> d = {"key2": 20, "key3": False}

# Return: dict
>>> rd | d
{'key1': 10, 'key2': 20, 'key3': False}
>>> d | rd
{'key2': 'abc', 'key3': False, 'key1': 10}

>>> rd |= d
>>> rd
rsdict({'key1': 10, 'key2': 20, 'key3': False}, frozen=False, fixkey=False, fixtype=True, cast=False)
# Add initial values of new keys only.
>>> rd.get_initial()
{'key1': 10, 'key2': 'abc', 'key3': False}
```

## Installation

```sh
pip install git+https://github.com/kihiyuki/python-rsdict.git
```

<!--
Develop branch:
pip install git+https://github.com/kihiyuki/python-rsdict.git@develop
-->
