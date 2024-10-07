import builtins
import struct
import parser.zerocode as zerocode  # local
import packet  # self
from xmlrpc.client import ServerProxy
from socket import socket, AF_INET, SOCK_DGRAM
from hashlib import md5
from uuid import UUID


def is_zerocoded(input: bytes) -> builtins.bool:
    """Expects bytes from the beginning of the packet."""
    return builtins.bool(input[0] & packet.ZEROCODED)


def is_reliable(input: bytes) -> builtins.bool:
    """Expects bytes from the beginning of the packet."""
    return builtins.bool(input[0] & packet.RELIABLE)


def is_resent(input: bytes) -> builtins.bool:
    """Expects bytes from the beginning of the packet."""
    return builtins.bool(input[0] & packet.RESENT)


def is_acknowledge(input: bytes) -> builtins.bool:
    """Expects bytes from the beginning of the packet."""
    return builtins.bool(input[0] & packet.ACKNOWLEDGE)


# Utility functions
def header(message: int, sequence: int, flags=0, extra_byte=0, extra_header=None):
    """Create a byte sequence for a packet header."""
    out = bytearray(struct.pack(">BLB", flags, sequence, extra_byte))
    if extra_header is not None:
        if extra_byte != len(header := bytes(extra_header)):
            raise Exception("Extra byte does not match extra header size.")
        out.extend(header)
    if (message & packet.low) == packet.low:
        out.extend(struct.pack(">L", message))
    elif (message & packet.medium) == packet.medium:
        out.extend(struct.pack(">H", message >> 16))
    elif (message & packet.high) == packet.high:
        out.extend(struct.pack(">B", message >> 24))
    else:
        raise Exception(f'Unexpected value in "message" arg. ({message})')
    return bytes(out)


def human_header(input: bytes) -> str:
    """
    Converts bytes into formatted string `'[123] {Low 123} +123 Resent Reliable Encoded Acknowledge'`
    """
    flags = input[0]
    sequence = int.from_bytes(input[1:5])
    extra = input[5]
    (mID, mHZ) = human_message(input)

    out = "".join(f"[{sequence}] ({mHZ} {mID}) +{extra}")
    # fmt: off
    if flags & packet.RESENT:      out += " Resent"
    if flags & packet.RELIABLE:    out += " Reliable"
    if flags & packet.ZEROCODED:   out += " Encoded"
    if flags & packet.ACKNOWLEDGE: out += " Acknowledge"
    # fmt: on
    return out


def sequence_number(input: bytes) -> int:
    """Expects bytes from the beginning of the packet."""
    return int.from_bytes(input[1:5])


def message_number(input: bytes) -> int:
    """
    Expects bytes from the beginning of the packet.
    Returns encoded message number and frequency.
    **Be sure to pass enough bytes to decode message ID.**
    """
    encoded = is_zerocoded(input)
    input = (
        zerocode.decode(input[packet.BODY_BYTE :])
        if encoded
        else input[packet.BODY_BYTE :]
    )

    # fmt: off
    if   input.startswith(b"\xff\xff\xff"): return int.from_bytes(input[:4])
    elif input.startswith(b"\xff\xff"):     return int.from_bytes(input[:4])
    elif input.startswith(b"\xff"):         return int.from_bytes(input[:2]) << 16
    else:                                   return int.from_bytes(input[:1]) << 24
    # fmt: on


def human_message(input: bytes) -> tuple[int, str]:
    """
    Expects bytes from the beginning of the packet.
    Converts message body into message ID and message frequency.
    **Be sure to pass enough bytes to decode message ID.**
    """
    encoded = is_zerocoded(input)
    input = (
        input[packet.BODY_BYTE :]
        if not encoded
        else zerocode.decode(input[packet.BODY_BYTE :])
    )

    # fmt: off
    if    input.startswith(b"\xff\xff\xff"): input = input[:4]
    elif  input.startswith(b"\xff\xff"):     input = input[:4]
    elif  input.startswith(b"\xff"):         input = input[:2]
    else: input = input[:1]

    id = int.from_bytes(input)

    if   0xFFFFFFFA <= id <= 0xFFFFFFFF: return (id, "Fixed")
    elif 0xFFFF0001 <= id <= 0xFFFFFFF9: return (id & 0xFFFF, "Low")
    elif 0x0000FF01 <= id <= 0x0000FFFE: return (id & 0x00FF, "Medium")
    elif 0x00000001 <= id <= 0x000000FE: return (id & 0x00FF, "High")
    # fmt: on
    raise Exception(f"{input} contained invalid message {id} ({hex(id)})")


def unpack_sequence(buffer, *args) -> list:
    """
    Calls `struct.unpack()` sequentially based on format string arguments.
    A previously unpacked value can be inserted into the next format string replacing `*`.
    Format strings resulting in multiple values are grouped as `tuple`.
    """

    def unpack_variable(buffer: bytes, format: str, offset: int) -> list:
        if (i := format.find("*")) != -1:
            first = format[0:i]
            v1 = struct.unpack_from(first, buffer, offset)
            second = str(v1[0]) + format[i + 1 :]
            v2 = struct.unpack_from(second, buffer, offset + struct.calcsize(first))
            return v1 + v2
        else:
            return struct.unpack_from(format, buffer, offset)

    out = []
    offset = 0
    last_val = None
    for format in map(str, args):
        # print('LOOP', format)
        if "*" in format:
            if last_val is not None:
                format = format.replace("*", str(last_val))
                if format == "0s":
                    out.append(b"")
                    last_val = None
                    continue
            elif format in ["<B*s", "<H*s"]:
                values = unpack_variable(buffer, format, offset)
                format = format.replace("*", str(values[0]))
                # print('UNPACKED VARIABLE', format, values)
                # print('UNPACKED BYTES', struct.calcsize(format))
        else:
            values = struct.unpack_from(format, buffer, offset)
        single = len(values) == 1
        # print(f'offset {offset:<4} format {format:<4} ahead {zerocode.byte2hex(buffer[offset:offset+4]):<11} {values[0] if single else values}')
        out.append(values[0] if single else values)
        last_val = values[0] if single else None
        # print('ADDING TO OFFSET', struct.calcsize(format))
        offset += struct.calcsize(format)
    return out


def pack_sequence(*args) -> bytes:
    """
    Calls `struct.pack()` sequentially based on alternating format string and value.
    A previously packed value can be inserted into the next format string replacing `*`.
    """
    out = bytearray()
    last_val = None
    i = 0
    while i < len(args):
        format, value, i = str(args[i]), args[i + 1], i + 2
        if "*" in format and last_val is not None:
            format = format.replace("*", str(last_val))
        if isinstance(value, tuple):
            out.extend(struct.pack(format, *value))
        else:
            value = value.encode() if isinstance(value, str) else value
            # print(f'format {format}:', type(value), value)
            out.extend(struct.pack(format, value))
        last_val = value
    return bytes(out)


# UDP client and connection/circuit manager
class client:
    """
    Interface for communicating with a region in Second Life.
    """

    _login_uri = "https://login.agni.lindenlab.com/cgi-bin/login.cgi"
    _login_proxy = ServerProxy(_login_uri)

    def send(self, *args):
        """
        Sends UDP data to connected socket.
        **Requires `login()` to be called first.**
        """
        self.sequence += 1
        return self.udp.send(b"".join(args))

    def receive(self):
        """
        Receives UDP data to connected socket.
        **Requires `login()` to be called first.**
        """
        return self.udp.recv(1024 * 64)

    def login(self, first: str, last: str, password: str):
        """
        Signs into Second Life and establishes a UDP connection with a region.
        """
        params = {
            "first": first,
            "last": last,
            "passwd": "$1$" + md5(password.encode()).hexdigest(),
            "start": "last",
            # client identification
            "channel": "login.py",
            "version": "0.0.0",
            "platform": "Win",
            # device identification
            "mac": "",
            "id0": "",
            "viewer_digest": "",
            "agree_to_tos": "true",
            "options": [],
        }
        self.login_response = self._login_proxy.login_to_simulator(params)
        self.udp_host = self.login_response["sim_ip"]
        self.udp_port = self.login_response["sim_port"]
        self.udp = socket(AF_INET, SOCK_DGRAM)
        self.udp.connect((self.udp_host, self.udp_port))
        self.sequence = 1

        # Pre-hash some persistent values.
        circuit_code = self.login_response["circuit_code"]
        session_id = self.login_response["session_id"]
        agent_id = self.login_response["agent_id"]
        self.circuit_code_bytes = struct.pack("i", circuit_code)
        self.session_id_bytes = UUID(session_id).bytes
        self.agent_id_bytes = UUID(agent_id).bytes

        return self.login_response
