import sys
from collections import namedtuple
from typing import Any, Optional


_KT = Any
_VT = Any
# _KT = Union[str, int, None]
# _VT = Union[str, int, float, str, bool, None, list, dict, tuple, Path]


class ErrorMessages(namedtuple(
    "ErrorMessages",
    ["frozen", "fixkey", "noattrib", "noarg"])
):
    def _replace(self, **kwargs):
        raise AttributeError("'ErrorMessages' has no attribute '_replace'")

    def _make(self, values):
        raise AttributeError("'ErrorMessages' has no attribute '_make'")


class Options(namedtuple(
    "Options",
    ["frozen", "fixkey", "fixtype", "cast"])
):
    def _replace(self, **kwargs):
        raise AttributeError("'Options' has no attribute '_replace'")

    def _make(self, values):
        raise AttributeError("'Options' has no attribute '_make'")


_ErrorMessages = ErrorMessages(
    frozen="Cannot assign to field of frozen instance",
    fixkey="If fixkey, cannot add or delete keys",
    noattrib="'rsdict' object has no attribute",
    noarg="'rsdict' has no argument named",
)


def check_option(name):
    def _check_option(func):
        def wrapper(self, *args, **kwargs):
            if self._get_option(name):
                raise AttributeError(_ErrorMessages.__getattribute__(name))
            return func(self, *args, **kwargs)
        return wrapper
    return _check_option


def check_instance(object, classinfo, classname: str = None) -> None:
    if classname is None:
        classname = classinfo.__name__
    if not isinstance(object, classinfo):
        raise TypeError(
            "expected {} instance, {} found".format(
                classname,
                type(object).__name__,
            )
        )


class _LimitedDict(dict):
    """Disable update, clear, setdefault, pop, popitem.
    """
    def update(self, *args, **kwargs) -> None:
        raise AttributeError("Attribute 'update' is disabled")

    # def clear(self) -> None:
    #     raise AttributeError("Attribute 'clear' is disabled")

    def setdefault(self, key: _KT, value: _VT = None) -> _VT:
        raise AttributeError("Attribute 'setdefault' is disabled")

    def pop(self, key: _KT) -> _VT:
        raise AttributeError("Attribute 'pop' is disabled")

    def popitem(self) -> tuple:
        raise AttributeError("Attribute 'popitem' is disabled")


class rsdict(dict):
    """Restricted and resetable dictionary,
    a subclass of Python dict (built-in dictionary).

    Examples:
        >>> from rsdict import rsdict
        >>> rd = rsdict(dict(foo=1, bar="baz"))
    """
    __initialized = False

    def __init__(
        self,
        items: dict,
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
        check_instance(items, dict)
        check_instance(frozen, int, classname="bool")
        check_instance(fixkey, int, classname="bool")
        check_instance(fixtype, int, classname="bool")
        check_instance(cast, int, classname="bool")

        # Store initial values
        self.__options = Options(
            frozen=bool(frozen),
            fixkey=bool(fixkey),
            fixtype=bool(fixtype),
            cast=bool(cast),
        )
        self.__inititems = _LimitedDict(items)

        self.__initialized = True
        return super().__init__(items)

    @check_option("fixkey")
    def __addkey(self, key: _KT, value: _VT) -> None:
        # add initialized key
        self.__inititems[key] = value
        # add current key
        return super().__setitem__(key, value)

    @check_option("fixkey")
    def __delkey(self, key: _KT) -> None:
        # delete initialized key
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
            elif self._get_option("fixtype"):
                if self._get_option("cast"):
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
    #     return super().__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in dir(self) and not name.startswith("_rsdict__"):
            pass
        elif not self.__initialized:
            pass
        else:
            raise AttributeError(
                "{} '{}'".format(
                    _ErrorMessages.noattrib,
                    name,
                )
            )
        return super().__setattr__(name, value)

    def __sizeof__(self) -> int:
        """Return size(current values) + size(initial values)"""
        # current values
        size = super().__sizeof__()
        # initial values
        size += self.get_initial().__sizeof__()
        size += self._get_option("frozen").__sizeof__()
        size += self._get_option("fixkey").__sizeof__()
        size += self._get_option("fixtype").__sizeof__()
        size += self._get_option("cast").__sizeof__()
        return size

    def __str__(self) -> str:
        """Return str(dict(current values))."""
        return str(self.to_dict())

    def __repr__(self) -> str:
        return "rsdict({}, frozen={}, fixkey={}, fixtype={}, cast={})".format(
            super().__repr__(),
            self._get_option("frozen"),
            self._get_option("fixkey"),
            self._get_option("fixtype"),
            self._get_option("cast"),
        )

    if sys.version_info >= (3, 9):
        # def __or__(self, other) -> dict:
        #     return super().__or__(other)

        @check_option("frozen")
        def __ior__(self, other) -> dict:
            """Return: rsdict"""
            if set(self.keys()) == set(self.keys() | other.keys()):
                return super().__ior__(other)
            elif self._get_option("fixkey"):
                raise AttributeError(_ErrorMessages.fixkey)
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
        """Convert to built-in dictionary (dict) instance.

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
            frozen = self._get_option("frozen")
        if fixkey is None:
            fixkey = self._get_option("fixkey")
        if fixtype is None:
            fixtype = self._get_option("fixtype")
        if cast is None:
            cast = self._get_option("cast")

        check_instance(reset, int, classname="bool")
        check_instance(frozen, int, classname="bool")
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
        # clear initialized key
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
        """Reset values to initial values.

        Args:
            key (optional): If None, reset all values.
        """
        if not self.is_changed():
            return None
        if key is None:
            items_init = self.get_initial()
            if self.keys() != items_init.keys():
                raise Exception("Some initial values are broken.")
        else:
            value = self.get_initial(key)
            items_init = {key: value}
        for k, v in items_init.items():
            self[k] = v

    def reset_all(self) -> None:
        """Alias of reset()."""
        self.reset()

    def get_initial(self, key: _KT = None) -> Any:
        """Return initial values.

        Args:
            key (optional): If None, get all values.

        Returns:
            dict (if key is None): Initial values.
            Any (else): Initial value.
        """
        if key is None:
            return self.__inititems
        else:
            return self.__inititems[key]

    def _get_option(self, name: str) -> bool:
        return self.__options.__getattribute__(name)

    def is_changed(self, key: _KT = None) -> bool:
        """Return whether the values are changed.

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
