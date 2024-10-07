from .packet import *


# fmt: off
class Frequency:
    size = 0
    base = 0

    def __and__(self, other: int) -> int:  return self.base & other
    def __or__(self, other: int) -> int:   return self.base | other
    def __add__(self, other: int) -> int:  return self.base + other
    def __eq__(self, other: int) -> int:   return self.base == other
    def __rand__(self, other: int) -> int: return other & self.base
    def __ror__(self, other: int) -> int:  return other | self.base
    def __radd__(self, other: int) -> int: return other + self.base
# fmt: on


class Fixed(Frequency):
    size = 4
    base = 0xFFFFFF00


class Low(Frequency):
    size = 4
    base = 0xFFFF0000


class Medium(Frequency):
    size = 2
    base = 0xFF000000


class High(Frequency):
    size = 1
    base = 0x00000000


class Format:
    size = 0
    format = ""
    zero = b"\x00" * size

    def __str__(self) -> str:
        return f"{self.format}"


class Uuid(Format):
    size = 16
    format = "16s"
    zero = UUID(int=0).bytes

    @staticmethod
    def from_bytes(data: bytes) -> str:
        """Returns a 36 character hex-string representation of the given bytes."""
        return str(UUID(bytes=data))

    @staticmethod
    def from_string(data: str) -> bytes:
        """Returns a bytes representation of the given hex-string. (Hyphens optional.)"""
        return UUID(hex=data).bytes


class String(Format):
    format = "*s"

    @staticmethod
    def from_bytes(data: bytes) -> str:
        return str(data, encoding="utf-8").rstrip("\x00")


class F32(Format):
    size = 4
    format = "<f"
    zero = b"\x00" * size
    zero_vector = zero * 3
    zero_rotation = zero * 4


class U32(Format):
    size = 4
    format = "<L"
    zero = b"\x00" * size


class U16(Format):
    size = 2
    format = "<H"
    zero = b"\x00" * size


class U8(Format):
    size = 1
    format = "<B"
    zero = b"\x00" * size


class Variable1(Format):
    size = 1
    format = "<B"
    zero = b"\x00" * size


class Variable2(Format):
    size = 2
    format = "<H"
    zero = b"\x00" * size


class Vector(Format):
    size = 4 * 3
    format = "<fff"
    zero = (0.0, 0.0, 0.0)


class Rotation(Format):
    size = 4 * 4
    format = "<ffff"
    zero = (0.0, 0.0, 0.0, 0.0)


class Bool(Format):
    size = 1
    format = "<B"
    zero = b"\x00" * size

    @staticmethod
    def from_bytes(data: bytes) -> builtins.bool:
        return builtins.bool(data)
