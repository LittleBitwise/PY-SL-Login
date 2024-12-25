import struct
from parser import zerocode

from message.data import (  # NOQA
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


# This Message class is primarily useful for decoding packet bytes into usable objects.
# It can of course be used for converting those objects into outgoing bytes.
# Static packets (such as screen dimensions and FOV) are easily packed directly.


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


class AgentThrottle(Message):
    _keys = {
        "AgentID": Uuid,
        "SessionID": Uuid,
        "CircuitCode": U32,
        "GenCounter": U32,
        "Throttles": Variable1,
    }
