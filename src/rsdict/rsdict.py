import sys
from collections import namedtuple
from typing import Any, Optional


# _KT = TypeVar("_KT")
# _VT = TypeVar("_VT")
_ErrorMessages = namedtuple(
    "_ErrorMessages",
    ["frozen", "fixkey", "noattrib", "noarg"]
)(
    frozen = "cannot assign to field of frozen instance",
    fixkey = "If fixkey, cannot add or delete keys",
    noattrib = "'rsdict' object has no attribute",
    noarg = "'rsdict' has no argument named",
)


def check_option(name):
    def _check_option(func):
        def wrapper(self, *args, **kwargs):
            if self.get_option(name):
                raise AttributeError(_ErrorMessages.__getattribute__(name))
            return func(self, *args, **kwargs)
        return wrapper
    return _check_option


class rsdict(dict):
    """Restricted and resetable dictionary,
    a subclass of Python dict (built-in dictionary).
    """
    def __init__(
        self,
        items: dict,
        frozen: bool = False,
        fixkey: bool = True,
        fixtype: bool = True,
        cast: bool = False,
    ) -> None:
        """Initialize rsdict instance with built-in dictionary items.

        Args:
            items (dict): Initial items.
                Built-in dictionary only. kwargs are not supported.
            frozen (bool, optional): If True, the instance will be frozen (read-only).
                Assigning to fields of frozen instance always raises AttributeError.
            fixkey: (bool, optional): If True, cannot add or delete keys.
            fixtype (bool, optional): if True, cannot change type of keys.
            cast (bool, optional): If False, cast to initial type (if possible).
                If True, allow only the same type of initial value.

        Examples:
            >>> user = rsdict(
            ...     dict(
            ...         name = "John",
            ...         enable = True,
            ...         count = 0,
            ...     ),
            ...     fixtype = False,
            ... )

            >>> user
            rsdict({'name': 'John', 'enable': True, 'count': 0},
                frozen=False, fixkey=True, fixtype=False, cast=False)
        """
        if not isinstance(items, dict):
            raise TypeError(
                "expected dict instance, {} found".format(
                    type(items).__name__,
                )
            )

        super().__init__(items)

        # Store initial values
        InitialValues = namedtuple(
            "InitialValues",
            ["items", "frozen", "fixkey", "fixtype", "cast"]
        )
        self.__initval = InitialValues(
            items = items.copy(),
            frozen = bool(frozen),
            fixkey = bool(fixkey),
            fixtype = bool(fixtype),
            cast = bool(cast),
        )

    @check_option("fixkey")
    def _addkey(self, key, value) -> None:
        # add initialized key
        items = self.get_initial()
        items[key] = value
        self.__initval = self.__initval._replace(items = items)
        return super().__setitem__(key, value)

    @check_option("fixkey")
    def _delkey(self, key) -> None:
        # delete initialized key
        items = self.get_initial()
        del items[key]
        self.__initval = self.__initval._replace(items = items)
        # delete current key
        return super().__delitem__(key)

    @check_option("frozen")
    def __setitem__(self, key: Any, value: Any) -> None:
        """Set value with key.

        Raises:
            AttributeError: If frozen, cannot change any values.
            AttributeError: If fixkey, cannot add new key.
            TypeError: If fixtype and not cast and type(value)!=type(initial_value).
            ValueError: If fixtype and failed in casting.
        """
        if key in self.keys():
            initialtype = type(self.get_initial()[key])
            if type(value) is initialtype:
                # type(value) is same as type(initial value)
                pass
            elif self.get_option("fixtype"):
                if self.get_option("cast"):
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
            return self._addkey(key, value)

    @check_option("frozen")
    def __delitem__(self, key: Any) -> None:
        """Cannot delete if fixkey or frozen."""
        return self._delkey(key)

    def __getattribute__(self, name: str) -> Any:
        # disable some attributes (of built-in dictionary)
        if name in ["fromkeys"]:
            raise AttributeError(
                "{} '{}'".format(
                    _ErrorMessages.noattrib,
                    name,
                )
            )
        return super().__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        enable = name in (
            dir(self) + ["_rsdict__initval"])

        if enable:
            return super().__setattr__(name, value)
        else:
            raise AttributeError(
                "{} '{}'".format(
                    _ErrorMessages.noattrib,
                    name,
                )
            )

    def __sizeof__(self) -> int:
        """Return size(current values) + size(initial values)"""
        # current values
        size = super().__sizeof__()
        # initial values
        size += self.get_initial().__sizeof__()
        size += self.get_option("frozen").__sizeof__()
        size += self.get_option("fixkey").__sizeof__()
        size += self.get_option("fixtype").__sizeof__()
        size += self.get_option("cast").__sizeof__()
        return size

    def __str__(self) -> str:
        """Return str(dict(current values))."""
        return str(self.to_dict())

    def __repr__(self) -> str:
        return "rsdict({}, frozen={}, fixkey={}, fixtype={}, cast={})".format(
            super().__repr__(),
            self.get_option("frozen"),
            self.get_option("fixkey"),
            self.get_option("fixtype"),
            self.get_option("cast"),
        )

    if sys.version_info >= (3, 9):
        # def __or__(self, other) -> dict:
        #     return super().__or__(other)

        @check_option("frozen")
        def __ior__(self, other):
            """Return: rsdict"""
            if set(self.keys()) == set(self.keys() | other.keys()):
                return super().__ior__(other)
            elif self.get_option("fixkey"):
                raise AttributeError(_ErrorMessages.fixkey)
            else:
                newkeys = (other.keys() | self.keys()) - self.keys()
                for key in newkeys:
                    self._addkey(key, other[key])
                return super().__ior__(other)

        # def __ror__(self, other):
        #     return super().__ror__(other)

    def set(self, key: Any, value: Any) -> None:
        """Alias of __setitem__."""
        return self.__setitem__(key, value)

    # def get(self, key: Any):

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
    ):
        """Return new rsdict instance.
        Both current values and initial values are copied.

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
            If the values are changed and copy with `reset=False, frozen=True` option,
            current (changed) values are copied as initial values and frozen.
        """
        if frozen is None:
            frozen = bool(self.get_option("frozen"))
        if fixkey is None:
            fixkey = bool(self.get_option("fixkey"))
        if fixtype is None:
            fixtype = bool(self.get_option("fixtype"))
        if cast is None:
            cast = bool(self.get_option("cast"))

        if not reset and frozen:
            # initialize with current values
            items = self.to_dict().copy()
        else:
            # initialize with initval values
            items = self.get_initial()

        # create new instance
        rd =  type(self)(
            items = items,
            frozen = frozen,
            fixkey = fixkey,
            fixtype = fixtype,
            cast = cast,
        )

        if reset:
            # no need to copy current values
            pass
        elif frozen:
            # cannnot copy (new instance is frozen)
            pass
        else:
            # copy current values
            for key in self.keys():
                rd[key] = self[key]
        return rd

    def update(self, *args, **kwargs) -> None:
        updates = dict(*args, **kwargs)
        for key, value in updates.items():
            self[key] = value

    @check_option("frozen")
    @check_option("fixkey")
    def clear(self) -> None:
        # clear initialized key
        items = self.get_initial()
        items.clear()
        self.__initval = self.__initval._replace(items = items)
        # clear current key
        return super().clear()

    def setdefault(self, key, value):
        # return super().setdefault(key, value)
        if key in self:
            return self[key]
        else:
            self[key] = value
            return value

    @check_option("frozen")
    @check_option("fixkey")
    def pop(self, key):
        return super().pop(key)

    @check_option("frozen")
    @check_option("fixkey")
    def popitem(self) -> tuple:
        return super().popitem()

    # TODO: (optional) check frozen deco
    def reset(self, key: Any = None) -> None:
        """Reset values to initial values.

        Args:
            key (Any): If None, reset all values.
        """
        if key is None:
            keys = self.keys()
        else:
            keys = [key]
        items_init = self.get_initial()
        for key_ in keys:
            self[key_] = items_init[key_]

    def reset_all(self) -> None:
        """Reset all values to initial values."""
        self.reset()

    def get_initial(self) -> dict:
        """Return initial values.

        Returns:
            dict: Initial values.
        """
        return self.__initval.items.copy()

    def get_option(self, name):
        if name in ["items"]:
            raise AttributeError("'{}' is not option".format(name))
        elif name not in self.__initval._fields:
            raise AttributeError(
                "{} '{}'".format(
                    _ErrorMessages.noarg,
                    name,
                )
            )
        else:
            return self.__initval.__getattribute__(name)

    def is_changed(self) -> bool:
        """Return whether the values are changed.

        Returns:
            bool: If True, the values are changed from initial.
        """
        return self.to_dict() != self.get_initial()


class rsdict_frozen(rsdict):
    """rsdict(fozen=True)"""
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
    """rsdict(fixkey=False, fixtype=False)"""
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
    """rsdict(fixkey=True, fixtype=False)"""
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
    """rsdict(fixkey=False, fixtype=True)"""
    def __init__(
        self,
        items: dict,
        frozen: bool = False,
        fixkey: bool = False,
        fixtype: bool = True,
        cast: bool = False
    ) -> None:
        return super().__init__(items, frozen, fixkey, fixtype, cast)
