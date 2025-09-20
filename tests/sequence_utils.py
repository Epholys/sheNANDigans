from typing import Any, Iterable, Sequence


def _to_list(x: Any) -> list[Any]:
    """Convert everything into a list:

    - string 'str' or bytes 'bytes' become '[str]' and '[bytes]
    - dictionaries become a list of items: '[(key1, value1), (key2, value2), ...]'
    - other iterables are converted to list.
    - single value become a singleton list.
    """
    match x:
        case str() | bytes():
            return [x]
        case dict():
            return list(x.items())
        case _ if isinstance(x, Iterable):
            return list(x)
        case _:
            return [x]


def _flatten(list: Sequence[Any]) -> list[Any]:
    """Flatten any sequence of objects.

    The objects does not need to be an iterable, they will be converted into a list.
    """
    return [item for sublist in list for item in _to_list(sublist)]
