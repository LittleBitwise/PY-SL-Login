import logging
import parser.template as template
import parser.zerocode as zerocode
import threading  # for user input
import time

import im as chat_util  # local
import packet as packet

logging.basicConfig(
    level=logging.DEBUG, format="\t%(levelname)s\t%(message)s\n", filename="dump.log"
)
log = logging.getLogger()

ignored_logging = [
    "LayerData",
    "SimulatorViewerTimeMessage",
    "ObjectUpdate",
    "ObjectUpdateCompressed",
    "ObjectUpdateCached" "ImprovedTerseObjectUpdate",
    "AvatarAnimation",
    "CoarseLocationUpdate",
    "PreloadSound",
    "AttachedSound",
    "ScriptControlChange",
    "StartPingCheck",
    "ViewerEffect",
]

client = packet.client()
client.login("firstname", "lastname", "password")

log.info("LOGGED IN")

# User input handler.

user_input = None

AGENT_CONTROL_TURN_LEFT = 0x02000000
AGENT_CONTROL_TURN_RIGHT = 0x04000000


def UserInputThread():
    global user_input
    while True:
        user_input = input()


def HandleUserInput():
    global user_input
    if user_input.lower() == "q":
        SendLogoutRequest()
        exit()
    if user_input == "A":
        log.info(f"sending input: {user_input}")
        SendAgentUpdate(AGENT_CONTROL_TURN_LEFT)
    elif user_input == "D":
        log.info(f"sending input: {user_input}")
        SendAgentUpdate(AGENT_CONTROL_TURN_RIGHT)
    elif user_input == "S":
        log.info(f"sending input: {user_input}")
        SendAgentUpdate(0)
    else:
        SendImprovedInstantMessage(user_input)
    user_input = None
    pass


user_input_thread = threading.Thread(
    name="user_input_thread", target=UserInputThread, daemon=True
)
user_input_thread.start()

# UDP messages.


def SendUseCircuitCode():
    client.send(
        packet.header(template.message["UseCircuitCode"], client.sequence),
        client.circuit_code_bytes,
        client.session_id_bytes,
        client.agent_id_bytes,
    )


def SendCompleteAgentMovement():
    client.send(
        packet.header(template.message["CompleteAgentMovement"], client.sequence),
        client.agent_id_bytes,
        client.session_id_bytes,
        client.circuit_code_bytes,
    )


def SendRegionHandshakeReply():
    client.send(
        packet.header(
            template.message["RegionHandshakeReply"], client.sequence, packet.ZEROCODED
        ),
        zerocode.encode_all(
            client.agent_id_bytes, client.session_id_bytes, packet.u32.zero
        ),
    )


class RegionHandshakeReply:
    pass


def SendRegionHandshakeReply():
    client.send(RegionHandshakeReply.to_bytes())


def SendAgentUpdate(control: int = 0):
    client.send(
        packet.header(
            template.message["AgentUpdate"], client.sequence, packet.ZEROCODED
        ),
        zerocode.encode_all(
            # client.agent_id_bytes,
            # client.session_id_bytes,
            # b'\x00' * 106,
            packet.pack_sequence(
                packet.uuid,
                client.agent_id_bytes,
                packet.uuid,
                client.session_id_bytes,
                packet.rotation,
                packet.rotation.zero,  # BodyRotation		16
                packet.rotation,
                packet.rotation.zero,  # HeadRotation		16
                packet.u8,
                0,  # State				1
                packet.vector,
                (128.0, 128.0, 30.0),  # CameraCenter		12
                packet.vector,
                (0.0, 1.0, 0.0),  # CameraAtAxis		12
                packet.vector,
                (1.0, 0.0, 0.0),  # CameraLeftAxis	12
                packet.vector,
                (0.0, 0.0, 1.0),  # CameraUpAxis		12
                packet.f32,
                16.0,  # Far				4
                packet.u32,
                control if control else 0,  # ControlFlags		4
                packet.u8,
                0,  # Flags				1
            )
        ),
    )


def SendCompletePingCheck(pingID: int):
    client.send(
        packet.header(template.message["CompletePingCheck"], client.sequence),
        packet.pack_sequence(packet.u8, pingID),
    )


def SendPacketAck(message_number: int):
    client.send(
        packet.header(template.message["PacketAck"], client.sequence),
        packet.pack_sequence(
            packet.u8,
            1,
            packet.u32,
            message_number,
        ),
    )


def SendLogoutRequest():
    client.send(
        packet.header(template.message["LogoutRequest"], client.sequence),
        client.agent_id_bytes,
        client.session_id_bytes,
    )


def SendAgentHeightWidth():
    client.send(
        packet.header(template.message["AgentHeightWidth"], client.sequence),
        client.agent_id_bytes,
        client.session_id_bytes,
        client.circuit_code_bytes,
        packet.pack_sequence(
            packet.u32,
            0,
            packet.u16,
            800,
            packet.u16,
            600,
        ),
    )


def SendAgentFOV():
    client.send(
        packet.header(template.message["AgentFOV"], client.sequence),
        client.agent_id_bytes,
        client.session_id_bytes,
        client.circuit_code_bytes,
        packet.pack_sequence(packet.u32, 0, packet.f32, 6.233185307179586),
    )


def SendChatFromViewer(text: str):
    log.info(f"Sending chat: {text}")
    client.send(
        packet.header(template.message["ChatFromViewer"], client.sequence),
        client.agent_id_bytes,
        client.session_id_bytes,
        chat_util.build_chat(text),
    )


def HandleChatFromSimulator(data: bytes):
    chat = chat_util.parse_chat(data)
    log.info(
        f"{chat.SourceType} {chat.Type} {chat.Audible} | {chat.FromName}: {chat.Message}"
    )
    if chat.Type <= chat_util.ChatType.Say:
        print(f"{chat.FromName}: {chat.Message}")


def HandleImprovedInstantMessage(data: bytes):
    im = chat_util.parse_im(data)
    log.info(im)
    if im.Dialog == chat_util.Dialog.IM:
        print(f"IM - {im.FromAgentName}: {im.Message}")


def SendImprovedInstantMessage(text: str):
    log.info(f"Sending IM: {text}")
    client.send(
        packet.header(
            template.message["ImprovedInstantMessage"],
            client.sequence,
            packet.ZEROCODED | packet.RELIABLE,
        ),
        zerocode.encode_all(
            chat_util.build_im(
                text,
                "llScriptProfiler Resident",
                client.agent_id_bytes,
                client.session_id_bytes,
                packet.uuid.from_string("779e1d56-5500-4e22-940a-cd7b5adddbe0"),
            )
        ),
    )


def HandleKickUser(data: bytes):
    data = packet.unpack_sequence(
        data[48:], packet.variable2.format, packet.string.format
    )
    reason = packet.string.from_bytes(data[-1])
    log.warning(f"Disconnected: {reason}")


def TimePassed(seconds: float) -> bool:
    present = time.time()
    earlier = getattr(TimePassed, "time", present)
    elapsed = (present - earlier) >= seconds
    TimePassed.time = present if elapsed else earlier
    return elapsed


# Login preamble.

SendUseCircuitCode()
SendCompleteAgentMovement()

# Main connection loop.

while data := client.receive():
    number = packet.message_number(data)
    message = template.message[number]

    if message not in ignored_logging:
        log.debug(
            "%s\t%s\n\tUDP: %s",
            packet.human_header(data),
            message,
            zerocode.byte2hex(data),
        )

    if packet.is_reliable(data):
        sequence_number = packet.sequence_number(data)
        SendPacketAck(sequence_number)

    if message == "StartPingCheck":
        [pingID] = packet.unpack_sequence(data[7:8], packet.u8)
        SendCompletePingCheck(pingID)

    if message == "RegionHandshake":
        SendRegionHandshakeReply()
        SendAgentUpdate()
        # SendAgentHeightWidth()
        # SendAgentFOV()

    if message == "ChatFromSimulator":
        HandleChatFromSimulator(data)

    if message == "ImprovedInstantMessage":
        HandleImprovedInstantMessage(data)

    # if TimePassed(0.5):
    # 	SendAgentUpdate()

    if message == "KickUser":
        HandleKickUser(data)
        break

    if user_input:
        HandleUserInput()
