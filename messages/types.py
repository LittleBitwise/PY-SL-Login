from pprint import pformat as pretty
from typing import Self
from uuid import UUID


class Format:
    zero = b""
    format = ""

    def __init__(self, value):
        self._data = value[0] if isinstance(value, tuple) else value

    def __str__(self):
        return f"{pretty(self._data)}"

    # def __repr__(self): return f'{pretty(self._data)}'

    @property
    def value(self):
        return self._data

    def alias(alias: str) -> Self:
        return {"Fixed": U32, "Low": U32, "Medium": U16, "High": U8}[alias]


# fmt: off
class U8(Format):  format = "<B"; size = 1; zero = b"\x00" * size
class S8(Format):  format = "<b"; size = 1; zero = b"\x00" * size
class U16(Format): format = "<H"; size = 2; zero = b"\x00" * size
class S16(Format): format = "<h"; size = 2; zero = b"\x00" * size
class U32(Format): format = "<I"; size = 4; zero = b"\x00" * size
class S32(Format): format = "<i"; size = 4; zero = b"\x00" * size
class F32(Format): format = "<f"; size = 4; zero = b"\x00" * size
class U64(Format): format = "<q"; size = 8; zero = b"\x00" * size
class S64(Format): format = "<Q"; size = 8; zero = b"\x00" * size
class F64(Format): format = "<d"; size = 8; zero = b"\x00" * size
# fmt: on


class Bool(U8):
    pass  # Boolean values identical to U8


class Vector(Format):
    format = "<fff"
    zero = (0.0, 0.0, 0.0)

    def __init__(self, value):
        expect = 3
        if expect != (length := len(value)):
            raise ValueError(f"Expected {expect} values, got {length}")
        self._data = value


class Rotation(Format):
    format = "<ffff"
    zero = (0.0, 0.0, 0.0, 0.0)

    def __init__(self, value):
        expect = 4
        if expect != (length := len(value)):
            raise ValueError(f"Expected {expect} values, got {length}")
        self._data = value


class Uuid(Format):
    format = "16s"
    zero = UUID(int=0).bytes

    def __init__(self, value: str | None = None):
        if isinstance(value, str):
            self._data = UUID(hex=value).bytes
        elif isinstance(value, bytes):
            self._data = UUID(bytes=value).bytes
        else:
            self._data = self.zero

    @property
    def bytes(self):
        return self._data

    @property
    def value(self):
        return str(UUID(bytes=self._data))

    # def __repr__(self) -> str:
    # 	return str(UUID(bytes=self._data))


class Variable1(Format):
    format = "<B*s"
    zero = b"\x00"

    def __init__(self, value):
        if len(value) != 2:
            raise ValueError(f"Expected 2 values, got {len(value)}")
        self._data = value

    def __str__(self) -> str:
        if isinstance(self._data[1], bytes):
            s = str(self._data[1], "utf-8", "replace")
        else:
            s = self._data[1]
        return f"[{self._data[0]}] {s}"

    @property
    def value(self):
        return str(self._data[1], "utf-8", "replace")

    @property
    def length(self):
        return self._data[0]


class Variable2(Variable1):
    format = "<H*s"
