from collections.abc import Mapping, MutableMapping


class CaseInsensitiveDict(MutableMapping):
    """
    A ``dict``-like object with case-insensitive keys if ``str``, ``bytes`` or ``bytearray`` is used. It behaves
    like an ordinary ``dict`` when other hashable types are used.

    The keys are stored in their original case and can be retrieved using the ``.keys()`` method. Lookup is done against
    both upper and lower case characters. This includes comparisons like ``ìn``.
    """
    @classmethod
    def _convert_key(cls, key):
        return key.lower() if isinstance(key, (str, bytes, bytearray)) else key

    def __init__(self, seq=None, **kwargs):
        self.__data = {}
        if seq is None:
            seq = {}
        self.update(seq, **kwargs)

    def __len__(self):
        return len(self.__data)

    def __getitem__(self, key):
        lookup_key = self.__class__._convert_key(key)
        return self.__data[lookup_key][1]

    def __setitem__(self, key, value):
        lookup_key = self.__class__._convert_key(key)
        self.__data[lookup_key] = (key, value)

    def __delitem__(self, key):
        lookup_key = self.__class__._convert_key(key)
        del self.__data[lookup_key]

    def __iter__(self):
        return (key for key, _ in self.__data.values())

    def __eq__(self, other):
        if isinstance(other, Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented

        return {self.__class__._convert_key(key): value for key, value in self.items()} == {other.__class__._convert_key(key): value for key, value in other.items()}

    def __str__(self):
        return str(dict(self.items()))

    def __repr__(self):
        return f"{self.__class__.__name__!s}({dict(self.items())!r})"

    def copy(self):
        return CaseInsensitiveDict(self.__data.values())

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d
