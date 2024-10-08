import struct
from parser import zerocode

from message.type import (  # NOQA
    F32,
    F64,
    S8,
    S16,
    S32,
    S64,
    U8,
    U16,
    U32,
    U64,
    Bool,
    Format,
    Rotation,
    Uuid,
    Variable1,
    Variable2,
    Vector,
)


class Message:
    _zerocoded = False
    _frequency = Format.alias("Low").size
    _keys = {}

    def __init__(self):
        self._data = dict.fromkeys(self._keys)

    def data(self, key: str):
        """Returns the underlying object being stored."""
        return self._data[key]

    def __getitem__(self, key: str):
        """Returns a textual representation of the stored value."""
        if key not in self._keys:
            raise KeyError(f"Key '{key}' not in {', '.join(self._keys)}")
        # print(f'Get self._data["{key}"] =', self._data[key].value)
        return self._data[key].value

    def __setitem__(self, key: str, value):
        if key not in self._keys:
            raise KeyError(f"Key `{key}` not in {', '.join(self._keys)}")
        expected = self._keys[key]
        if not isinstance(value, expected):
            raise ValueError(f"{key} value `{value}` is not {expected}")
        self._data[key] = value
        # print(f'Set self._data["{key}"] =', value.value)

    def __str__(self):
        out = ""
        for k, v in self._data.items():
            if not isinstance(v, (Variable1, Variable2)):
                out += f"{k}: {v.value}\n"
            else:
                out += f"{k}: [{v.length}] {v.value}\n"
        return out

    # def __repr__(self):
    # 	return pretty(self._data, sort_dicts=False)


class StartPingCheck(Message):
    _frequency = Format.alias("High").size
    _keys = {
        "PingID": U8,
        "OldestUnacked": U32,
    }


class AgentMovementComplete(Message):
    _keys = {
        "AgentID": Uuid,
        "SessionID": Uuid,
        "Position": Vector,
        "LookAt": Vector,
        "RegionHandle": U64,
        "Timestamp": U32,
        "ChannelVersion": Variable2,
    }


class ChatFromSimulator(Message):
    _keys = {
        "FromName": Variable1,
        "SourceID": Uuid,
        "OwnerID": Uuid,
        "SourceType": U8,
        "ChatType": U8,
        "Audible": U8,
        "Position": Vector,
        "Message": Variable2,
    }


class ImprovedInstantMessage(Message):
    _zerocoded = True
    _keys = {
        "AgentID": Uuid,
        "SessionID": Uuid,
        "FromGroup": Bool,
        "ToAgentID": Uuid,
        "ParentEstateID": U32,
        "RegionID": Uuid,
        "Position": Vector,
        "Offline": U8,
        "Dialog": U8,
        "ID": Uuid,
        "Timestamp": U32,
        "FromAgentName": Variable1,
        "Message": Variable2,
        "BinaryBucket": Variable2,
    }


class RegionHandshake(Message):
    _zerocoded = True
    _keys = {
        "RegionFlags": U32,
        "SimAccess": U8,
        "SimName": Variable1,
        "SimOwner": Uuid,
        "IsEstateManager": Bool,
        "WaterHeight": F32,
        "BillableFactor": F32,
        "CacheID": Uuid,
        "TerrainBase0": Uuid,
        "TerrainBase1": Uuid,
        "TerrainBase2": Uuid,
        "TerrainBase3": Uuid,
        "TerrainDetail0": Uuid,
        "TerrainDetail1": Uuid,
        "TerrainDetail2": Uuid,
        "TerrainDetail3": Uuid,
        "TerrainStartHeight00": F32,
        "TerrainStartHeight01": F32,
        "TerrainStartHeight10": F32,
        "TerrainStartHeight11": F32,
        "TerrainHeightRange00": F32,
        "TerrainHeightRange01": F32,
        "TerrainHeightRange10": F32,
        "TerrainHeightRange11": F32,
        "RegionID": Uuid,
        "CPUClassID": S32,
        "CPURatio": S32,
        "ColoName": Variable1,
        "ProductSKU": Variable1,
        "ProductName": Variable1,
        "RegionInfo4": (
            Variable1,
            {  # repeat following block N times
                "RegionFlagsExtended": U64,
                "RegionProtocols": U64,
            },
        ),
    }


class RegionHandshakeReply(Message):
    _zerocoded = True
    _keys = {
        "AgentID": Uuid,
        "SessionID": Uuid,
        "Flags": U32,
    }


class AgentUpdate(Message):
    _zerocoded = True
    _keys = {
        "AgentID": Uuid,
        "SessionID": Uuid,
        "BodyRotation": Rotation,
        "HeadRotation": Rotation,
        "State": U8,
        "CameraCenter": Vector,
        "CameraAtAxis": Vector,
        "CameraLeftAxis": Vector,
        "CameraUpAxis": Vector,
        "Far": F32,
        "ControlFlags": U32,
        "Flags": U8,
    }


class KickUser(Message):
    _keys = {
        "TargetIP": U8,
        "TargetPort": U16,
        "AgentID": Uuid,
        "SessionID": Uuid,
        "Reason": Variable2,
    }


@classmethod
def _from_bytes(cls: Message, data: bytes):
    """Parses packet bytes according to message fields."""

    def unpack_sequence(buffer: bytes, *args):
        """Unpacks bytes from buffer according to struct format strings"""
        out = []
        offset = 0
        last_val = None
        for format in map(str, args):
            # print(f'FORMAT {format:<4}', 'AHEAD', zerocode.byte2hex(buffer[offset:offset+4]), 'OFFSET', offset) # NOQA
            if format == Variable1.format:
                [length] = struct.unpack_from(U8.format, buffer, offset)
                # print('VAR1 LENGTH', str(length))
                [string] = struct.unpack_from(f"{str(length)}s", buffer, offset + 1)
                out.append((length, string))
                last_val = None
                offset += 1 + length
                continue
            if format == Variable2.format:
                [length] = struct.unpack_from(U16.format, buffer, offset)
                # print('VAR2 LENGTH', str(length))
                [string] = struct.unpack_from(f"{str(length)}s", buffer, offset + 2)
                out.append((length, string))
                last_val = None
                offset += 2 + length
                continue
            if "*" in format and last_val is not None:
                format = format.replace("*", str(last_val))
            if format == "0s":
                out.append(b"")
                last_val = None
                continue
            values = struct.unpack_from(format, buffer, offset)
            single = len(values) == 1
            out.append(values[0] if single else values)
            last_val = values[0] if single else None
            offset += struct.calcsize(format)
        return out

    message = cls()
    body_byte = 6
    # print('CLASS', type(message), 'IN', __class__)
    # print('KEYS', message._keys)
    # print('VALUES', message._keys.values())
    formats = []
    for x in message._keys.values():
        if not isinstance(x, tuple):
            formats.append(x.format)
        else:
            repeat: Variable1 = x[0]
            raise Exception("TODO: solve for variable length blocks")
            block: dict = x[1]
            for _ in range(repeat):
                for y in block.values():
                    formats.append(y.format)
    # print('FORMATS', formats)
    if message._zerocoded:
        data = data[body_byte:]
        data = zerocode.decode(data)
        # print(zerocode.byte2hex(data))
        data = data[message._frequency :]
        unpacked = unpack_sequence(data, *formats)
    else:
        data = data[body_byte + message._frequency :]
        # print(zerocode.byte2hex(data))
        unpacked = unpack_sequence(data, *formats)

    # print('UNPACKED', unpacked)
    for i, (name, impl) in enumerate(message._keys.items()):  # assign
        # print('ASSIGN', name, unpacked[i], impl, '->', impl(unpacked[i]))
        message[name] = impl(unpacked[i])
    return message


def _to_bytes(self: Message):
    out = bytearray()

    # for i, (name, impl) in enumerate(self._keys.items()):
    for name, impl in self._keys.items():
        data = self.data(name)
        # print("CONVERTING", name, data.value, impl)

        if isinstance(data.value, (int, float)):
            out.extend(struct.pack(data.format, data.value))
        elif isinstance(data, (Variable1, Variable2)):
            _format = data.format[:2]
            out.extend(struct.pack(_format, data.length))
            _format = f"{data.length}s"
            out.extend(struct.pack(_format, data.value.encode()))
        elif isinstance(data, Uuid):
            out.extend(data.bytes)
        elif isinstance(data, Vector):
            out.extend(struct.pack(Vector.format, *data.value))
        elif isinstance(data, Rotation):
            out.extend(struct.pack(Rotation.format, *data.value))
        else:
            raise Exception("Unexpected data", data)
        # print('\t', type(value))
        # out.extend(value)

    if self._zerocoded:
        out = zerocode.encode(out)
    return bytes(out)


Message.to_bytes = _to_bytes
Message.from_bytes = _from_bytes
