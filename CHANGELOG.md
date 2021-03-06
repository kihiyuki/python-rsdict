# Change Log

<!-- TEMPLATE
## v0.0.0

**Implemented enhancements:**
**Fixed bugs:**
**Closed issues:**
**Merged pull requests:**
-->

## v0.1.8

- Use deepcopy for initial items.

## v0.1.7

- Add option argument.: `get_option(key)`
- Add support for `fromdict`.

## v0.1.6

- Make `__setitem__` faster. (74times of dict -> x22)
- Make `__addkey` faster. (x49 -> x5)
- Make `__delkey` faster. (x49 -> x5)

## v0.1.5

- Add typechecking for initial arguments.
- Add optional argument.: `get_initval(key)`

## v0.1.4

- Add subclasses `rsdict_frozen`, `rsdict_unfix`, `rsdict_fixkey`, `rsdict_fixtype`.

## v0.1.3

- Add Python3.5 support.
- Make it possible to create new rsdict with rsdict.

## v0.1.2

- Fix `get()`.
- Fix type checking.

## v0.1.1

- Fix `__setattr__()`.

## v0.1.0

- Key-restriction can be switched.
- Add initializing argument 'fixkey'.
- Type-restriction can be switched.
- Add initializing argument 'fixtype' (as replacement for 'strict').
- Add initializing argument 'cast'.
- Use GitHub Actions (Python package).
- Add support for `__ior__()`, `clear()`, `setdefault()`, `pop()`, `popitem()`, `del`.
- Improve test.
