import sys
import copy
from collections import namedtuple
from typing import Any, Optional, Union


_KT = Any
_VT = Any
# _KT = Union[str, int, None]
# _VT = Union[str, int, float, str, bool, None, list, dict, tuple, Path]


class _Raise(object):
    @staticmethod
    def attribute(*args, **kwargs) -> None:
        raise AttributeError("No such attribute")

    @staticmethod
    def attribute_set(*args, **kwargs) -> None:
        raise AttributeError("Cannot set attribute")


class _Inititems(dict):
    update = setdefault = pop = popitem = _Raise.attribute

    def __init__(self, items: dict) -> None:
        return super().__init__(copy.deepcopy(items))

    def __setitem__(self, key: _KT, value: _VT) -> None:
        if key in self:
            # cannot change existing value
            _Raise.attribute_set()
        return super().__setitem__(key, copy.deepcopy(value))


class _Options(
    namedtuple(
        "Options",
        ["frozen", "fixkey", "fixtype", "cast"])):
    _make = _replace = _Raise.attribute


class _ErrorMessages(
    namedtuple(
        "ErrorMessages",
        _Options._fields)):
    _make = _replace = _Raise.attribute


_ERRORMESSAGES = _ErrorMessages(
    frozen="Cannot assign to field of frozen instance",
    fixkey="If fixkey, cannot add or delete keys",
    fixtype="",
    cast="",
)


def check_option(name: str):
    """Decorator for checking _Options.

    Args:
        name (str): Fieldname of _Options class.

    Raises:
        AttributeError: If the option parameter is True.
    """
    def _check_option(func):
        def wrapper(self, *args, **kwargs):
            if self.__getattribute__(name):
                raise AttributeError(_ERRORMESSAGES.__getattribute__(name))
            return func(self, *args, **kwargs)
        return wrapper
    return _check_option


def _check_instance(object, classinfo, classname: str = None) -> None:
    """Check type of object by `isinstance`.

    Args:
        classname (str, optional): Name of expected type.

    Raises:
        TypeError: If `isinstance()` is False.
    """
    if classname is None:
        classname = classinfo.__name__
    if not isinstance(object, classinfo):
        raise TypeError(
            "expected {} instance, {} found".format(
                classname,
                type(object).__name__,
            )
        )


class rsdict(dict):
    """Restricted and resetable dictionary,
    a subclass of Python dict (built-in dictionary).

    Examples:
        >>> from rsdict import rsdict
        >>> rd = rsdict(dict(foo=1, bar="baz"))
    """
    def __init__(
        self,
        items: Union[dict, "rsdict"],
        frozen: bool = False,
        fixkey: bool = True,
        fixtype: bool = True,
        cast: bool = False,
    ) -> None:
        """Initialize rsdict instance
        with data(dict) and optional arguments(bool).

        Args:
            items (dict): Initial items (data).
                Built-in dictionary only. kwargs are not supported.
            frozen (bool, optional): If True,
                the instance will be frozen (immutable).
            fixkey (bool, optional): If True,
                cannot add or delete keys.
            fixtype (bool, optional): If True,
                cannot change type of keys.
            cast (bool, optional): If False,
                cast to initial type (if possible).
                If True, allow only the same type of initial value.

        Examples:
            >>> rd = rsdict(
            ...     dict(
            ...         name = "John",
            ...         enable = True,
            ...     ),
            ...     fixtype = False,
            ... )
            >>> rd
            rsdict({'name': 'John', 'enable': True},
                frozen=False, fixkey=True, fixtype=False, cast=False)
        """
        # check argument types
        _check_instance(items, dict)
        _check_instance(frozen, int, classname="bool")
        _check_instance(fixkey, int, classname="bool")
        _check_instance(fixtype, int, classname="bool")
        _check_instance(cast, int, classname="bool")

        # create Options object
        self.__options = _Options(
            frozen=bool(frozen),
            fixkey=bool(fixkey),
            fixtype=bool(fixtype),
            cast=bool(cast),
        )

        # NOTE: Cannot deepcopy restdict
        if type(items) is type(self):
            items = items.to_dict()

        # store initial values in __inititems
        if self.frozen:
            self.__inititems = None
        else:
            self.__inititems = _Inititems(items)

        return super().__init__(items)

    @property
    def frozen(self) -> bool:
        return self.__options.frozen

    @property
    def fixkey(self) -> bool:
        return self.__options.fixkey

    @property
    def fixtype(self) -> bool:
        return self.__options.fixtype

    @property
    def cast(self) -> bool:
        return self.__options.cast

    @check_option("fixkey")
    def __addkey(self, key: _KT, value: _VT) -> None:
        """Add a new key to instance."""
        # add initial key
        self.__inititems[key] = value
        # add current key
        return super().__setitem__(key, value)

    @check_option("fixkey")
    def __delkey(self, key: _KT) -> None:
        """Delete a key from instance."""
        # delete initial key
        del self.__inititems[key]
        # delete current key
        return super().__delitem__(key)

    @check_option("frozen")
    def __setitem__(self, key: _KT, value: _VT) -> None:
        """Set value with key.

        Raises:
            AttributeError: If frozen, cannot change any values.
            AttributeError: If fixkey, cannot add new key.
            TypeError: If fixtype and not cast
                and type(value)!=type(initial_value).
            ValueError: If fixtype and failed in casting.
        """
        if key in self:
            initialtype = type(self.get_initial(key))
            if type(value) is initialtype:
                # type(value) is same as type(initial value)
                pass
            elif self.fixtype:
                if self.cast:
                    # raise if failed
                    value = initialtype(value)
                else:
                    raise TypeError(
                        "expected {} instance, {} found".format(
                            initialtype.__name__,
                            type(value).__name__,
                        )
                    )
            # change value
            return super().__setitem__(key, value)
        else:
            # add a new key
            return self.__addkey(key, value)

    @check_option("frozen")
    def __delitem__(self, key: _KT) -> None:
        """Cannot delete if fixkey or frozen."""
        return self.__delkey(key)

    # def __getattribute__(self, name: str) -> Any:
    #     print("__getattribute__", name)
    #     return super().__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        try:
            _ = self.__inititems
        except Exception:
            pass
        else:
            if name in dir(self) and not name.startswith("_rsdict__"):
                pass
            else:
                _Raise.attribute_set()
        return super().__setattr__(name, value)

    def __sizeof__(self) -> int:
        """Return size(current values) + size(initial values)"""
        # current values
        size = super().__sizeof__()
        # initial values
        size += self.__inititems.__sizeof__()
        size += self.frozen.__sizeof__()
        size += self.fixkey.__sizeof__()
        size += self.fixtype.__sizeof__()
        size += self.cast.__sizeof__()
        return size

    def __str__(self) -> str:
        return str(self.to_dict())

    def __repr__(self) -> str:
        return "rsdict({}, frozen={}, fixkey={}, fixtype={}, cast={})".format(
            super().__repr__(),
            self.frozen,
            self.fixkey,
            self.fixtype,
            self.cast,
        )

    if sys.version_info >= (3, 9):
        # def __or__(self, other) -> dict:
        #     return super().__or__(other)

        @check_option("frozen")
        def __ior__(self, other) -> dict:
            if set(self.keys()) == set(self.keys() | other.keys()):
                return super().__ior__(other)
            elif self.fixkey:
                raise AttributeError(_ERRORMESSAGES.fixkey)
            else:
                newkeys = (other.keys() | self.keys()) - self.keys()
                for key in newkeys:
                    self.__addkey(key, other[key])
                return super().__ior__(other)

        # def __ror__(self, other):
        #     return super().__ror__(other)

    def set(self, key: _KT, value: _VT) -> None:
        """Alias of __setitem__."""
        return self.__setitem__(key, value)

    # def get(self, key: _KT) -> _VT:

    def to_dict(self) -> dict:
        """Convert to built-in dictionary instance.

        Returns:
            dict: Current values.
        """
        return super().copy()

    def copy(
        self,
        reset: bool = False,
        frozen: Optional[bool] = None,
        fixkey: Optional[bool] = None,
        fixtype: Optional[bool] = None,
        cast: Optional[bool] = None,
    ) -> "rsdict":
        """Create new rsdict instance,
        copy current values and initial values.
        Optional arguments can be changed.

        Args:
            reset (bool, optional): If True,
                current values are not copied.
            frozen (bool, optional): If set,
                the argument of new instance will be overwritten.
            fixkey (bool, optional): (Same as above.)
            fixtype (bool, optional): (Same as above.)
            cast (bool, optional): (Same as above.)

        Returns:
            rsdict: New instance.

        Note:
            If the values are changed and copy with
            `reset=False, frozen=True` option,
            current values are copied as initial values and frozen.
        """
        if frozen is None:
            frozen = self.frozen
        if fixkey is None:
            fixkey = self.fixkey
        if fixtype is None:
            fixtype = self.fixtype
        if cast is None:
            cast = self.cast

        _check_instance(reset, int, classname="bool")
        _check_instance(frozen, int, classname="bool")
        if not reset and frozen:
            # initialize with current values
            items = self.to_dict().copy()
        else:
            # initialize with initial values
            items = self.get_initial()

        # create new instance
        rdnew = self.__class__(
            items=items,
            frozen=frozen,
            fixkey=fixkey,
            fixtype=fixtype,
            cast=cast,
        )

        if reset or frozen:
            # no need to copy current values
            pass
        # elif self.is_changed():
        else:
            # copy current values
            for key in self:
                if self.is_changed(key):
                    rdnew[key] = self[key]
        return rdnew

    def update(self, *args, **kwargs) -> None:
        updates = dict(*args, **kwargs)
        for key, value in updates.items():
            self[key] = value

    @check_option("frozen")
    @check_option("fixkey")
    def clear(self) -> None:
        # clear initial key
        self.__inititems.clear()
        # clear current key
        return super().clear()

    def setdefault(self, key: _KT, value: _VT = None) -> _VT:
        if key in self:
            return self[key]
        else:
            self[key] = value
            return value

    @check_option("frozen")
    @check_option("fixkey")
    def pop(self, key: _KT) -> _VT:
        return super().pop(key)

    @check_option("frozen")
    @check_option("fixkey")
    def popitem(self) -> tuple:
        return super().popitem()

    @classmethod
    def fromkeys(cls, keys: _KT, value: _VT = None) -> "rsdict":
        return cls(dict.fromkeys(keys, value))

    def reset(self, key: _KT = None) -> None:
        """Reset value(s) to initial value(s).

        Args:
            key (optional): If None, reset all values.
        """
        if not self.is_changed():
            return None
        if key is None:
            items_init = self.get_initial()
            if self.keys() != items_init.keys():
                raise UnboundLocalError(
                    "Current and initial keys do not match"
                )
        else:
            value = self.get_initial(key)
            items_init = {key: value}
        for k, v in items_init.items():
            self[k] = v

    def reset_all(self) -> None:
        """Alias of reset()."""
        self.reset()

    def get_initial(self, key: _KT = None) -> Any:
        """Get initial value(s).

        Args:
            key (optional): If None, get all values.

        Returns:
            dict (if key is None): Initial values.
            Any (else): Initial value.
        """
        if self.frozen:
            ret = self
        else:
            ret = self.__inititems
        if key is None:
            return ret
        else:
            return ret[key]

    def is_changed(self, key: _KT = None) -> bool:
        """Return whether the value(s) are changed.

        Args:
            key (optional): If not None, check the key only.

        Returns:
            bool: If True, the values are changed from initial.
        """
        if key is None:
            return self != self.get_initial()
        else:
            return self[key] != self.get_initial(key)


class rsdict_frozen(rsdict):
    """rsdict(fozen=True)

    Examples:
        >>> from rsdict import rsdict_frozen as rsdict
    """
    def __init__(
        self,
        items: dict,
        frozen: bool = True,
        fixkey: bool = True,
        fixtype: bool = True,
        cast: bool = False
    ) -> None:
        return super().__init__(items, frozen, fixkey, fixtype, cast)


class rsdict_unfix(rsdict):
    """rsdict(fixkey=False, fixtype=False)

    Examples:
        >>> from rsdict import rsdict_unfix as rsdict
    """
    def __init__(
        self,
        items: dict,
        frozen: bool = False,
        fixkey: bool = False,
        fixtype: bool = False,
        cast: bool = False
    ) -> None:
        return super().__init__(items, frozen, fixkey, fixtype, cast)


class rsdict_fixkey(rsdict):
    """rsdict(fixkey=True, fixtype=False)

    Examples:
        >>> from rsdict import rsdict_fixkey as rsdict
    """
    def __init__(
        self,
        items: dict,
        frozen: bool = False,
        fixkey: bool = True,
        fixtype: bool = False,
        cast: bool = False
    ) -> None:
        return super().__init__(items, frozen, fixkey, fixtype, cast)


class rsdict_fixtype(rsdict):
    """rsdict(fixkey=False, fixtype=True)

    Examples:
        >>> from rsdict import rsdict_fixtype as rsdict
    """
    def __init__(
        self,
        items: dict,
        frozen: bool = False,
        fixkey: bool = False,
        fixtype: bool = True,
        cast: bool = False
    ) -> None:
        return super().__init__(items, frozen, fixkey, fixtype, cast)
