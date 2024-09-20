import struct
import zerocode # local
from xmlrpc.client import ServerProxy
from socket import socket, AF_INET, SOCK_DGRAM
from hashlib import md5
from uuid import UUID

# Common constants
ZEROCODED   = 0x80
RELIABLE    = 0x40
RESENT      = 0x20
ACKNOWLEDGE = 0x10

BODY_BYTE = 6

class Frequency:
	size = 0;
	base = 0;
	def __and__(self, other: int) -> int: return self.base & other
	def __or__(self, other: int) -> int: return self.base | other
	def __add__(self, other: int) -> int: return self.base + other
	def __eq__(self, other: int) -> int: return self.base == other
	def __rand__(self, other: int) -> int: return other & self.base
	def __ror__(self, other: int) -> int: return other | self.base
	def __radd__(self, other: int) -> int: return other + self.base

class Fixed(Frequency):
	size = 4
	base = 0xffffff00
class Low(Frequency):
	size = 4
	base = 0xffff0000
class Medium(Frequency):
	size = 2
	base = 0xff000000
class High(Frequency):
	size = 1
	base = 0x00000000

fixed = Fixed()
low = Low()
medium = Medium()
high = High()

class Format:
	size = 0
	format = ''
	zero = b'\x00' * size
	def __str__(self) -> str: return f'{self.format}'

class Uuid(Format):
	size = 16
	format = '16s'
	zero = UUID(int=0)
	@staticmethod
	def from_bytes(data: bytes) -> str:
		"""Returns a 36 character hex-string representation of the given bytes."""
		return str(UUID(bytes=data))
	@staticmethod
	def from_string(data: str) -> bytes:
		"""Returns a bytes representation of the given hex-string. (Hyphens optional.)"""
		return UUID(hex=data).bytes
class String(Format):
	format = '*s'
	@staticmethod
	def from_bytes(data: bytes) -> str:
		return str(data, encoding='utf-8').rstrip('\x00')
class F32(Format):
	size = 4
	format = 'f'
	zero = b'\x00' * size
	zero_vector = zero * 3
	zero_rotation = zero * 4
class U32(Format):
	size = 4
	format = 'L'
	zero = b'\x00' * size
class U16(Format):
	size = 2
	format = 'H'
	zero = b'\x00' * size
class U8(Format):
	size = 1
	format = 'B'
	zero = b'\x00' * size
class Variable1(Format):
	size = 1
	format = 'B'
	zero = b'\x00' * size
class Variable2(Format):
	size = 2
	format = '<H'
	zero = b'\x00' * size
class Vector(Format):
	size = 4 * 3
	format = '<fff'
	zero = b'\x00' * size
class Rotation(Format):
	size = 4 * 4
	format = '<ffff'
	zero = b'\x00' * size

string = String()
uuid = Uuid()
f32 = F32()
u32 = U32()
u16 = U16()
u8 = U8()
variable1 = Variable1()
variable2 = Variable2()
vector = Vector()
rotation = Rotation()

# Common message IDs
UseCircuitCode        = low | 3
RegionHandshakeReply  = low | 149
UUIDNameRequest       = low | 235
CompleteAgentMovement = low | 249
CompletePingCheck     = high | 2
AgentUpdate           = high | 4
PacketAck             = 0xFFFFFFFB

def is_zerocoded(input: bytes) -> bool:
	"""Expects bytes from the beginning of the packet."""
	return bool(input[0] & ZEROCODED)

def is_reliable(input: bytes) -> bool:
	"""Expects bytes from the beginning of the packet."""
	return bool(input[0] & RELIABLE)

def is_resent(input: bytes) -> bool:
	"""Expects bytes from the beginning of the packet."""
	return bool(input[0] & RESENT)

def is_acknowledge(input: bytes) -> bool:
	"""Expects bytes from the beginning of the packet."""
	return bool(input[0] & ACKNOWLEDGE)

# Utility functions
def header(message: int, sequence: int, flags=0, extra_byte=0, extra_header=None):
	"""Create a byte sequence for a packet header."""
	out = bytearray(struct.pack('>BLB', flags, sequence, extra_byte))
	if extra_header is not None:
		if extra_byte != len(header := bytes(extra_header)):
			raise Exception('Extra byte does not match extra header size.')
		out.extend(header)
	if   (message & low) == low:       out.extend(struct.pack('>L', message))
	elif (message & medium) == medium: out.extend(struct.pack('>H', message >> 16))
	elif (message & high) == high:     out.extend(struct.pack('>B', message >> 24))
	else: raise Exception(f'Unexpected value in "message" arg. ({message})')
	return bytes(out)

def human_header(input: bytes) -> str:
	"""
	Converts bytes into formatted string `'[123] {Low 123} +123 Resent Reliable Encoded Acknowledge'`
	"""
	flags = input[0]
	sequence = int.from_bytes(input[1:5])
	extra = input[5]
	(mID, mHZ) = human_message(input)

	out = ''.join(f'[{sequence}] ({mHZ} {mID}) +{extra}')
	if flags & RESENT:      out += ' Resent'
	if flags & RELIABLE:    out += ' Reliable'
	if flags & ZEROCODED:   out += ' Encoded'
	if flags & ACKNOWLEDGE: out += ' Acknowledge'
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
	input = input[BODY_BYTE:] if not encoded else zerocode.decode(input[BODY_BYTE:])
	if    input.startswith(b'\xff\xff\xff'): return int.from_bytes(input[:4])
	elif  input.startswith(b'\xff\xff'):     return int.from_bytes(input[:4])
	elif  input.startswith(b'\xff'):         return int.from_bytes(input[:2]) << 16
	else:                                    return int.from_bytes(input[:1]) << 24


def human_message(input: bytes) -> tuple[int, str]:
	"""
	Expects bytes from the beginning of the packet.
	Converts message body into message ID and message frequency.
	**Be sure to pass enough bytes to decode message ID.**
	"""
	encoded = is_zerocoded(input)
	input = input[BODY_BYTE:] if not encoded else zerocode.decode(input[BODY_BYTE:])
	if    input.startswith(b'\xff\xff\xff'): input = input[:4]
	elif  input.startswith(b'\xff\xff'):     input = input[:4]
	elif  input.startswith(b'\xff'):         input = input[:2]
	else:                                    input = input[:1]

	id = int.from_bytes(input)

	if   0xFFFFFFFA <= id <= 0xFFFFFFFF: return (id, 'Fixed')
	elif 0xFFFF0001 <= id <= 0xFFFFFFF9: return (id & 0xFFFF, 'Low')
	elif 0x0000FF01 <= id <= 0x0000FFFE: return (id & 0x00FF, 'Medium')
	elif 0x00000001 <= id <= 0x000000FE: return (id & 0x00FF, 'High')
	raise Exception(f'{input} contained invalid message {id} ({hex(id)})')

def unpack_sequence(buffer, *args) -> list:
	"""
	Calls `struct.unpack()` sequentially based on format string arguments.
	A previously unpacked value can be inserted into the next format string replacing `*`.
	Format strings resulting in multiple values are grouped as `tuple`.
	"""
	out = []
	offset = 0
	last_val = None
	for format in map(str, args):
		if '*' in format and last_val is not None:
			format = format.replace('*', str(last_val))
		values = struct.unpack_from(format, buffer, offset)
		offset += struct.calcsize(format)
		single = len(values) == 1
		out.append(values[0] if single else values)
		last_val = values[0] if single else None
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
		format, value, i = str(args[i]), args[i+1], i + 2
		if '*' in format and last_val is not None:
			format = format.replace('*', str(last_val))
		out.extend(struct.pack(format, value)) # todo: string values to bytes
		last_val = value
	return bytes(out)

# UDP client and connection/circuit manager
class client:
	"""
	Interface for communicating with a region in Second Life.
	"""
	_login_uri = 'https://login.agni.lindenlab.com/cgi-bin/login.cgi'
	_login_proxy = ServerProxy(_login_uri)

	def send(self, *args):
		"""
		Sends UDP data to connected socket.
		**Requires `login()` to be called first.**
		"""
		self.sequence += 1
		return self.udp.send(b''.join(args))

	def receive(self):
		"""
		Receives UDP data to connected socket.
		**Requires `login()` to be called first.**
		"""
		return self.udp.recv(1024*64)

	def login(self, first: str, last: str, password: str):
		"""
		Signs into Second Life and establishes a UDP connection with a region.
		"""
		params = {
			'first': first,
			'last': last,
			'passwd': '$1$' + md5(password.encode()).hexdigest(),
			'start': 'last',
			# client identification
			'channel': 'login.py',
			'version': '0.0.0',
			'platform': 'Win',
			# device identification
			'mac': '',
			'id0': '',
			'viewer_digest': '',
			'agree_to_tos': 'true',
			'options': [],
		}
		self.login_response = self._login_proxy.login_to_simulator(params)
		self.udp_host = self.login_response['sim_ip']
		self.udp_port = self.login_response['sim_port']
		self.udp = socket(AF_INET, SOCK_DGRAM)
		self.udp.connect((self.udp_host, self.udp_port))
		self.sequence = 1

		# Pre-hash some persistent values.
		circuit_code = self.login_response['circuit_code']
		session_id   = self.login_response['session_id']
		agent_id     = self.login_response['agent_id']
		self.circuit_code_bytes = struct.pack('i', circuit_code)
		self.session_id_bytes   = UUID(session_id).bytes
		self.agent_id_bytes     = UUID(agent_id).bytes

		return self.login_response
