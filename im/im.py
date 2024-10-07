from typing import NamedTuple
from enum import IntEnum
from time import time
from uuid import UUID, uuid4 as generate_uuid
import packet as packet, parser.zerocode as zerocode  # local


# Instant messages


class Dialog(IntEnum):
    IM = 0
    NOTIFICATION_OK = 1
    NOTIFICATION_COUNTDOWN = 2
    GROUP_INVITE = 3
    INVENTORY_OFFER = 4
    INVENTORY_OFFER_ACCEPTED = 5
    INVENTORY_OFFER_DECLINED = 6
    GROUP_MESSAGE_TO_ALL = 8
    OBJECT_INVENTORY_OFFER = 9
    OBJECT_INVENTORY_OFFER_ACCEPTED = 10
    OBJECT_INVENTORY_OFFER_DECLINED = 11
    SESSION_INVITE = 13
    SESSION_INVITE_P2P = 14
    SESSION_START_GROUP = 15
    SESSION_START_CONFERENCE = 16
    SESSION_SEND_MESSAGE = 17
    SESSION_LEAVE = 18
    IM_FROM_OBJECT = 19
    IM_AUTORESPONSE = 20
    SHOW_IN_CONSOLE_HISTORY = 21
    TELEPORT_OFFER = 22
    TELEPORT_RESPONSE_A = 23
    TELEPORT_RESPONSE_B = 24
    IM_NO_EMAIL = 31
    IM_GROUP_ANNOUNCEMENT = 32
    IM_TYPING_STARTED = 41
    IM_TYPING_STOPPED = 42


class ImprovedInstantMessage(NamedTuple):
    AgentID: str
    SessionID: str
    FromGroup: bool
    ToAgentID: str
    ParentEstateID: int
    RegionID: str
    Position: tuple
    Offline: int
    Dialog: int
    ID: str
    Timestamp: int
    FromAgentNameLen: int
    FromAgentName: str
    MessageLen: int
    Message: str
    BinaryBucketLen: int
    BinaryBucket: bytes


def parse_im(data: bytes) -> ImprovedInstantMessage:
    data = packet.unpack_sequence(
        zerocode.decode(data[6:])[4:],
        packet.uuid,
        packet.uuid,
        packet.bool,
        packet.uuid,
        packet.u32,
        packet.uuid,
        packet.vector,
        packet.u8,
        packet.u8,
        packet.uuid,
        packet.u32,
        packet.variable1,
        packet.string,
        packet.variable2,
        packet.string,
        packet.variable2,
        packet.string,
    )
    return ImprovedInstantMessage(
        packet.uuid.from_bytes(data[0]),
        packet.uuid.from_bytes(data[1]),
        packet.bool.from_bytes(data[2]),
        packet.uuid.from_bytes(data[3]),
        data[4],
        packet.uuid.from_bytes(data[5]),
        data[6],
        data[7],
        data[8],
        packet.uuid.from_bytes(data[9]),
        data[10],
        data[11],
        packet.string.from_bytes(data[12]),
        data[13],
        packet.string.from_bytes(data[14]),
        data[15],
        zerocode.byte2hex(data[16]),
    )


def build_im(
    text: str, agent_name: str, agent_id: bytes, session_id: bytes, to_agent_id: bytes
) -> bytes:
    agent_name_bytes = agent_name.encode("utf-8") + b"\x00"
    text_bytes = text.encode("utf-8") + b"\x00"
    return packet.pack_sequence(
        packet.uuid,
        agent_id,
        packet.uuid,
        session_id,
        packet.bool,
        False,
        packet.uuid,
        to_agent_id,
        packet.u32,
        0,
        packet.uuid,
        packet.uuid.zero,
        packet.vector,
        packet.vector.zero,
        packet.u8,
        0,
        packet.u8,
        0,
        packet.uuid,
        compute_session_id(Dialog.IM, agent_id, to_agent_id),
        packet.u32,
        int(time()),
        packet.variable1,
        len(agent_name_bytes),
        packet.string,
        agent_name_bytes,
        packet.variable2,
        len(text_bytes),
        packet.string,
        text_bytes,
        packet.variable2,
        0,
        packet.string,
        b"",
        packet.u32,
        0,
    )


# Local chat


class ChatFromSimulator(NamedTuple):
    FromNameLen: int
    FromName: str
    SourceID: str
    OwnerID: str
    SourceType: int
    Type: int
    Audible: int
    Position: tuple
    MessageLen: int
    Message: str


class SourceType(IntEnum):
    System = 0
    Agent = 1
    Object = 2


class Audible(IntEnum):
    Not = -1
    Barely = 0
    Fully = 1


class ChatType(IntEnum):
    Whisper = 0
    Normal = 1
    Shout = 2
    Say = 3
    StartTyping = 4
    StopTyping = 5
    Debug = 6
    OwnerSay = 8


def parse_chat(data) -> ChatFromSimulator:
    data = packet.unpack_sequence(
        data[10:],
        packet.variable1,
        packet.string,
        packet.uuid,
        packet.uuid,
        packet.u8,
        packet.u8,
        packet.u8,
        packet.vector,
        packet.variable2,
        packet.string,
    )
    print("parse_chat data", data)
    return ChatFromSimulator(
        data[0],
        packet.string.from_bytes(data[1]),
        packet.uuid.from_bytes(data[2]),
        packet.uuid.from_bytes(data[3]),
        data[4],
        data[5],
        data[6],
        data[7],
        data[8],
        packet.string.from_bytes(data[9]),
    )


def build_chat(text: str, channel=0, type=1):
    text_bytes = text.encode("utf-8") + b"\x00"
    return packet.pack_sequence(
        packet.variable2,
        len(text_bytes),
        packet.string,
        text_bytes,
        packet.u8,
        type,
        packet.u32,
        channel,
    )


# Sessions


def compute_session_id(dialog: int, agent_id: bytes, other_agent_id: bytes) -> bytes:
    if dialog != Dialog.IM:
        if dialog in {Dialog.SESSION_INVITE, Dialog.SESSION_START_GROUP}:
            return other_agent_id
        if agent_id == other_agent_id:
            return agent_id
        if dialog == Dialog.SESSION_START_CONFERENCE:
            return generate_uuid().bytes
    a = int.from_bytes(agent_id)
    b = int.from_bytes(other_agent_id)
    return UUID(int=a ^ b).bytes


if __name__ == "__main__":
    print(
        compute_session_id(
            Dialog.IM,
            packet.uuid.from_string("28c5efb6-fcaa-4ed5-9cf1-a640d1a99272"),
            packet.uuid.from_string("779e1d56-5500-4e22-940a-cd7b5adddbe0"),
        )
    )
