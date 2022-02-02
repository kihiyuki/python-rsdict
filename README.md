# rsdict

[![Actions Badge - Python package](https://github.com/kihiyuki/python-rsdict/actions/workflows/python-package.yml/badge.svg)](https://github.com/kihiyuki/python-rsdict/actions/workflows/python-package.yml)
[![PyPI version](https://badge.fury.io/py/rsdict.svg)](https://badge.fury.io/py/rsdict)
[![Downloads](https://static.pepy.tech/personalized-badge/rsdict?period=total&units=international_system&left_color=grey&right_color=blue&left_text=PyPI%20Downloads)](https://pepy.tech/project/rsdict)

<!-- ref: rsdict.__doc__ -->
rsdict is a **restricted** and **resetable** dictionary,
a subclass of `dict` (inherits from built-in dictionary).

```python
>>> from rsdict import rsdict

>>> d = {"foo": 0, "bar": "baz"}
>>> rd = rsdict(d)
>>> rd
rsdict({'foo': 0, 'bar': 'baz'}, frozen=False, fixkey=True, fixtype=True, cast=False)

# fixkey=True: key restriction
>>> rd["newkey"] = 1
AttributeError
# fixtype=True: type restriction
>>> rd["foo"] = "str.value"
TypeError

>>> rd["foo"] = 999
>>> rd == d
False
# reset values to initial
>>> rd.reset()
>>> rd == d
True
```

## Installation

```sh
pip install rsdict
```

## Features

- Type-restrict(able): If activated, every type of value is fixed to its initial type.
- Key-restrict(able): If activated, cannot add or delete keys.
- Resettable: to initial value(s).

### Arguments

`rsdict(items, frozen=False, fixkey=True, fixtype=True, cast=False)`

<!-- ref: rsdict.__init__.__doc__ -->
- items (dict): Initial items (data).
    Built-in dictionary only. kwargs are not supported.
- frozen (bool, optional): If True,
    the instance will be frozen (immutable).
- fixkey (bool, optional): If True,
    cannot add or delete keys.
- fixtype (bool, optional): If True,
    cannot change type of keys.
- cast (bool, optional): If False,
    cast to initial type (if possible).
    If True, allow only the same type of initial value.

### Subclasses

```python
# rsdict(frozen=True) as default
from rsdict import rsdict_frozen as rsdict

# rsdict(fixkey=False, fixtype=False) as default
from rsdict import rsdict_unfix as rsdict

# rsdict(fixkey=True, fixtype=False) as default
from rsdict import rsdict_fixkey as rsdict

# rsdict(fixkey=False, fixtype=True) as default
from rsdict import rsdict_fixtype as rsdict
```

### Additional methods

- `set(key, value)`: Alias of `__setitem__`.
- `to_dict() -> dict`: Convert to dict instance.
- `reset(key: Optional[Any]) -> None`: Reset value to the initial value.
    If key is None, reset all values.
- `is_changed() -> bool`: If True, the values are changed from initial.
- `get_initial(key: Optional[Any]) -> dict | Any`: Return initial value(s).
    If key is None, Return dict of all initial values.

### Disabled methods

<!-- ref: rsdict.__getattribute__ -->
- `fromkeys()`

### Notes

- Expected types of value:
    `int`, `float`, `str`, `bool`, `None`,
    `list`, `dict`, `tuple`,
    `pathlib.Path`
- Some types (e.g. `numpy.ndarray`) cannot be cast.
- [Tested in Python3.5, 3.6, 3.7, 3.8, 3.9, 3.10.](https://github.com/kihiyuki/python-rsdict/actions/workflows/python-package.yml)

## Examples

### Create (Initialize)

<!-- from rsdict.__init__.__doc__ -->
```python
>>> from rsdict import rsdict

>>> d = dict(
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
>>> rd["xyz"]
KeyError
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
# (Change some values.)
>>> rd["enable"] = False
>>> rd["count"] = 5
>>> rd.is_changed()
True

# Reset with a key.
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

### Copy

```python
# Create a new rsdict with different optional arguments.
# If reset, copy initial values only.
>>> rd["name"] = "Mike"
>>> rd2 = rd.copy(reset=True)
>>> rd2 == rd.get_initial()
True

# If frozen and not reset, copy current values as new initial values.
>>> rd3 = rd.copy(frozen=True)
>>> rd3
rsdict({'name': 'Mike', 'enable': True, 'count': 0},
    frozen=True, fixkey=True, fixtype=False, cast=False)
>>> rd3 == rd
True
>>> rd3.get_initial() == rd.get_initial()
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

(Python3.9 or later)

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

## Speed

![speed.png](doc/_static/speed.png)
