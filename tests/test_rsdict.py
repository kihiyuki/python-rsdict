import sys
import math
from itertools import product
from pathlib import Path, PosixPath, WindowsPath

import pytest

from src.rsdict import rsdict


OptionNames = ["frozen", "fixkey", "fixtype", "cast"]
Patterns = dict()
for i, p in zip(
    range(len(OptionNames)**2),
    product([False, True], repeat=len(OptionNames))
):
    k = "P" + str(i).zfill(len(str(len(OptionNames)**2 - 1)))
    d = dict()
    for opt, p_val in zip(OptionNames, p):
        d[opt] = p_val
    Patterns[k] = d.copy()
ParamKwargs = ( "kwargs", list(Patterns.values()))
ParamNames = list(Patterns.keys())
# test data
InitItems = {
    "int": 0,
    "float": 1.1,
    "list": ["hello"],
    "dict": dict(a=2),
    "tuple": (5, 6),
    "set": {7, 8},
    "str": "abc",
    "path": Path("./lib"),
    0: True,
}


@pytest.fixture(scope="session", autouse=False)
def inititems():
    return InitItems


@pytest.fixture(scope="function", autouse=False)
def defaultdata():
    return rsdict(InitItems)


def compare(x, x_init):
    if isinstance(x, float):
        return math.isclose(x, x_init)
    else:
        return x == x_init


class Testrsdict(object):
    def test_type(self, defaultdata):
        assert type(defaultdata) is rsdict
        assert type(defaultdata) is not dict
        assert isinstance(defaultdata, rsdict)
        assert isinstance(defaultdata, dict)

    @pytest.mark.parametrize(*ParamKwargs, ids=ParamNames)
    def test_init(self, kwargs, inititems):
        data = rsdict(inititems, **kwargs)
        assert data.to_dict() == inititems
        for arg in kwargs.keys():
            assert data.get_option(arg) == kwargs[arg]

        # unsupported dict-style initialization
        with pytest.raises(TypeError):
            data = rsdict(a=1, b="xyz")
        with pytest.raises(TypeError):
            data = rsdict((("int", 2), ("str", "xyz")))

    def test_dict(self, defaultdata, inititems):
        """test attributes equivalent to (built-in) dict"""
        assert defaultdata == inititems
        assert defaultdata.keys() == inititems.keys()

        for v, v_init in zip(defaultdata.values(), inititems.values()):
            assert compare(v, v_init)
        for kv, kv_init in zip(defaultdata.items(), inititems.items()):
            k, v = kv
            k_init, v_init = kv_init
            assert compare(k, k_init)
            assert compare(v, v_init)

        assert list(defaultdata) == list(inititems)
        assert "int" in defaultdata
        assert "hoge" not in defaultdata

        if sys.version_info >= (3, 8):
            # reverse
            assert list(reversed(defaultdata)) == list(defaultdata.keys())[::-1]

    def test_dict_or(self):
        if sys.version_info >= (3, 9):
            # __or__
            rd = rsdict(dict(a="hello", b="bye"))
            d = dict(a=5, c=True)
            assert type(rd | d) is dict
            assert type(d | rd) is dict
            assert rd | d == dict(a=5, b="bye", c=True)
            assert d | rd == dict(a="hello", b="bye", c=True)

            # __ior__
            rd_ior = rd.copy(frozen=True)
            with pytest.raises(AttributeError):
                rd_ior |= d

            rd_ior = rd.copy(fixkey=True)
            with pytest.raises(AttributeError):
                rd_ior |= d
            rd_ior |= dict(a=5)
            assert rd_ior.to_dict() == (rd.to_dict() | dict(a=5))
            assert rd_ior.get_initial() == rd.get_initial()

            rd_ior = rd.copy(fixkey=False)
            rd_ior |= d
            assert rd_ior.to_dict() == (rd.to_dict() | d)
            assert rd_ior.get_initial() == (d | rd.get_initial())

    def test_get(self, defaultdata, inititems):
        assert defaultdata.get("int") == inititems.get("int")
        assert defaultdata["int"] == inititems["int"]

        # key not exists
        assert defaultdata.get("hoge") is None
        with pytest.raises(KeyError):
            _ = defaultdata["hoge"]

        # getattr is not allowed
        with pytest.raises(AttributeError):
            _ = defaultdata.int

    @pytest.mark.parametrize(*ParamKwargs, ids=ParamNames)
    def test_del(self, kwargs, inititems):
        data = rsdict(inititems, **kwargs)
        if kwargs["frozen"] or kwargs["fixkey"]:
            # AttributeError: cannot delete any keys
            with pytest.raises(AttributeError):
                del data["int"]
            with pytest.raises(AttributeError):
                del data.int
        else:
            del data["int"]
            assert "int" not in data

        del data

    @pytest.mark.parametrize(("key", "val_set", "val_get"), [
        ("int", -1, -1),
        ("int", 2.6, 2),
        ("int", "3", 3),
        ("float", -1, -1.0),
        ("float", "0.5", 0.5),
        ("list", list(), []),
        ("list", range(5), list(range(5))),
        ("list", dict(a=1, b=2), ["a", "b"]),
        ("dict", dict(), dict()),
        ("dict", (("g", 3), ("h", 5)), {"g": 3, "h": 5}),
        ("tuple", (), ()),
        ("tuple", [9, 3], (9, 3)),
        ("set", set(), set()),
        ("set", [9, 3], {3, 9}),
        ("str", "xyz", "xyz"),
        ("str", 5.5, "5.5"),
        ("str", None, "None"),
        ("path", Path("data"), Path("data")),
        ("path", "data", Path("data")),
        (0, 0, False),
    ])
    @pytest.mark.parametrize(*ParamKwargs, ids=ParamNames)
    def test_set(self, kwargs, key, val_set, val_get, inititems):
        data = rsdict(inititems, **kwargs)
        val_cast = type(val_set) is not type(val_get)
        if kwargs["frozen"]:
            with pytest.raises(AttributeError):
                data[key] = val_set
            with pytest.raises(AttributeError):
                data.set(key, val_set)
            return
        elif not kwargs["fixtype"]:
            pass
        elif val_cast and not kwargs["cast"]:
            with pytest.raises(TypeError):
                data[key] = val_set
            with pytest.raises(TypeError):
                data.set(key, val_set)
            return

        data[key] = val_set
        if kwargs["fixtype"]:
            assert compare(val_get, data[key])
        else:
            assert compare(val_set, data[key])

        data.set(key, val_set)
        if kwargs["fixtype"]:
            assert compare(val_get, data[key])
        else:
            assert compare(val_set, data[key])

    @pytest.mark.parametrize(*ParamKwargs, ids=ParamNames)
    def test_set_addkey(self, kwargs, inititems):
        data = rsdict(inititems, **kwargs)
        if kwargs["frozen"] or kwargs["fixkey"]:
            with pytest.raises(AttributeError):
                data["hoge"] = "hoge"
        else:
            data["hoge"] = "hoge"
            assert not data.is_changed()
            assert data.get_initial()["hoge"] == "hoge"

    @pytest.mark.parametrize(*ParamKwargs, ids=ParamNames)
    def test_set_raise(self, kwargs, inititems):
        data = rsdict(inititems, **kwargs)
        # setattr is not allowed
        with pytest.raises(AttributeError):
            data.int = 99

        if kwargs["frozen"]:
            # cannot set frozen instance
            with pytest.raises(AttributeError):
                data["int"] = 5
            return

        if kwargs["fixtype"]:
            # cannot cast
            with pytest.raises(Exception):
                data["int"] = "hoge"
            # cannot cast
            with pytest.raises(TypeError):
                data["float"] = None

    @pytest.mark.parametrize(*ParamKwargs, ids=ParamNames)
    def test_update(self, kwargs, inititems):
        data = rsdict(inititems, **kwargs)
        if not kwargs["frozen"] and not kwargs["fixkey"]:
            # add new key
            data.update(hoge=50)
            assert data["hoge"] == 50
            data.update({"hoge": 2, "fuga": 3})
            assert data["hoge"] == 2
            assert data["fuga"] == 3
        else:
            # cannot add new key
            with pytest.raises(AttributeError):
                data.update(hoge=50)
            with pytest.raises(AttributeError):
                data.update({"hoge": 2, "fuga": 3})

        # frozen
        if kwargs["frozen"]:
            # cannot update existing key
            with pytest.raises(AttributeError):
                data.update(int=50)
            with pytest.raises(AttributeError):
                data.update({"int": 5, "str": 5})
            return

        # update by kwargs
        data.update(int=50)
        assert data["int"] == 50

        # update by dict
        if kwargs["fixtype"]:
            if kwargs["cast"]:
                data.update({"int": 5, "str": 5})
                assert data["int"] == 5
                assert data["str"] == "5"
            else:
                with pytest.raises(TypeError):
                    data.update({"int": 5, "str": 5})
        else:
            data.update({"int": "5", "str": 5})
            assert data["int"] == "5"
            assert data["str"] == 5

    def test_reset(self, defaultdata, inititems):
        assert not defaultdata.is_changed()
        assert defaultdata.to_dict() == defaultdata.get_initial()

        # change
        defaultdata["int"] = 9
        defaultdata["str"] = "cde"
        defaultdata[0] = False
        assert defaultdata["str"] != inititems["str"]
        assert defaultdata != inititems
        assert defaultdata.is_changed()
        assert defaultdata.to_dict() != defaultdata.get_initial()

        # partially reset
        defaultdata.reset("str")
        assert defaultdata["str"] == inititems["str"]
        assert defaultdata.is_changed()

        # reset_all
        data = defaultdata.copy()
        data.reset()
        assert not data.is_changed()
        assert data == inititems
        data = defaultdata.copy()
        data.reset_all()
        assert not data.is_changed()
        assert data == inititems

    @pytest.mark.parametrize(*ParamKwargs, ids=ParamNames)
    def test_copy_option(self, kwargs, defaultdata):
        # change option
        data = defaultdata.copy(**kwargs)
        assert data == defaultdata
        for arg in kwargs.keys():
            assert data.get_option(arg) == kwargs[arg]

    @pytest.mark.parametrize(*ParamKwargs, ids=ParamNames)
    def test_copy_reset(self, kwargs, inititems):
        data = rsdict(inititems, **kwargs)

        if not kwargs["frozen"]:
            # change
            data["int"] = 99
            data["str"] = "cde"
            if not kwargs["fixtype"]:
                data["list"] = False

        # reset=True
        data2 = data.copy(reset=True)
        assert not data2.is_changed()
        assert data2.to_dict() == data.get_initial()
        assert data2.get_initial() == data.get_initial()

        # reset=False(default)
        data2 = data.copy()
        if kwargs["frozen"]:
            assert not data2.is_changed()
        else:
            assert data2.is_changed()
        assert data2 == data
        assert data2.get_initial() == data.get_initial()

        # reset=False, frozen=True
        if kwargs["frozen"]:
            pass
        else:
            data2 = data.copy(frozen=True)
            assert not data2.is_changed()
            assert data2.to_dict() == data.to_dict()
            assert data2.get_initial() == data.to_dict()

    @pytest.mark.parametrize(*ParamKwargs, ids=ParamNames)
    def test_delkey(self, kwargs, inititems):
        data = rsdict(inititems, **kwargs)
        if kwargs["frozen"] or kwargs["fixkey"]:
            with pytest.raises(AttributeError):
                del data["int"]
            with pytest.raises(AttributeError):
                data.pop("str")
            with pytest.raises(AttributeError):
                data.popitem()
            with pytest.raises(AttributeError):
                data.clear()
        else:
            del data["int"]
            assert data.pop("str") == inititems["str"]
            k = list(data.keys())[-1]
            assert data.popitem() == (k, inititems[k])
            data.clear()
            assert data.to_dict() == dict()
            assert data.get_initial() == dict()
            data.reset()
            assert data.to_dict() == dict()

    @pytest.mark.parametrize(*ParamKwargs, ids=ParamNames)
    def test_setdefault(self, kwargs, inititems):
        data = rsdict(inititems, **kwargs)
        # key already exists
        assert data.setdefault("int", 99) == inititems["int"]

        if kwargs["frozen"] or kwargs["fixkey"]:
            with pytest.raises(AttributeError):
                ret = data.setdefault("hoge", "fuga")
        else:
            # add new key
            ret = data.setdefault("hoge", "fuga")
            assert ret == "fuga"
            assert data["hoge"] == ret
            assert data.get_initial()["hoge"] == ret

    @pytest.mark.parametrize(*ParamKwargs, ids=ParamNames)
    def test_disabled(self, kwargs, inititems):
        data = rsdict(inititems, **kwargs)
        with pytest.raises(AttributeError):
            _ = data.fromkeys(["a", "b"], 1)

    @pytest.mark.parametrize(*ParamKwargs, ids=ParamNames)
    def test_other(self, kwargs, inititems):
        data = rsdict(inititems, **kwargs)

        # repr()
        data_eval = eval(data.__repr__())
        assert data_eval == data
        # str()
        assert str(data) == str(inititems)
        # sizeof
        assert data.__sizeof__() > 0

        # items is not an option
        with pytest.raises(AttributeError):
            data.get_option("items")
        # invalid option name
        with pytest.raises(AttributeError):
            data.get_option("hoge")
        with pytest.raises(AttributeError):
            data.hoge = 0

        # restricted attribute
        with pytest.raises(AttributeError):
            _ = data.__initval
        with pytest.raises(AttributeError):
            _ = data.__addkey
        with pytest.raises(AttributeError):
            _ = data.__delkey
        with pytest.raises(AttributeError):
            data.__initval = 0
        with pytest.raises(AttributeError):
            data.__addkey = 0
        with pytest.raises(AttributeError):
            data.__delkey = 0
