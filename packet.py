import xmlrpc.client, socket, struct, hashlib
import zerocode # local
from uuid import UUID

# Common constants
ZEROCODED   = 0x80
RELIABLE    = 0x40
RESENT      = 0x20
ACKNOWLEDGE = 0x10

zero_rot_bytes = struct.pack('<ffff', 0.0, 0.0, 0.0, 0.0)
zero_vec_bytes = struct.pack('<fff', 0.0, 0.0, 0.0)
zero_f_bytes = struct.pack('<f', 0.0)
zero_4_bytes = struct.pack('>L', 0)
zero_1_bytes = struct.pack('>B', 0)

def check_zerocoded(input: bytes) -> bool:
	return bool(input[0] & ZEROCODED)

def check_reliable(input: bytes) -> bool:
	return bool(input[0] & RELIABLE)

def check_resent(input: bytes) -> bool:
	return bool(input[0] & RESENT)

def check_acknowledge(input: bytes) -> bool:
	return bool(input[0] & ACKNOWLEDGE)

# Utility functions
def header(message: int, sequence: int, flags=0, extra_byte=0, extra_header=None):
	"""
	Create a byte sequence for a packet header.
	"""
	out = bytearray(struct.pack('>BLB', flags, sequence, extra_byte))
	if extra_header is not None:
		if extra_byte != len(header := bytes(extra_header)):
			raise Exception('Extra byte does not match extra header size.')
		out.extend(header)
	out.extend(struct.pack('>L', message))
	return bytes(out)

def human_header(input: bytes) -> str:
	"""
	Converts bytes into formatted string `'[123] {Low 123} +123 Resent Reliable Encoded Acknowledge'`
	"""
	flags = input[0]
	sequence = int.from_bytes(input[1:5])
	extra = input[5]
	(mID, mHZ) = message_id_from_bytes(input[6:12])

	out = ''.join(f'[{sequence}] ({mHZ} {mID}) +{extra}')
	if check_resent(flags):      out += ' Resent'
	if check_reliable(flags):    out += ' Reliable'
	if check_zerocoded(flags):   out += ' Encoded'
	if check_acknowledge(flags): out += ' Acknowledge'
	return out

def message_id_from_bytes(input: bytes, encoded: bool=False) -> tuple[int, str]:
	"""
	Converts message body into message ID and message frequency.
	**Be sure to pass enough bytes to decode message ID.**
	"""
	if encoded: input = zerocode.decode(input)
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

# UDP client and connection/circuit manager
class client:
	"""
	Interface for communicating with a region in Second Life.
	"""
	_login_uri = 'https://login.agni.lindenlab.com/cgi-bin/login.cgi'
	_login_proxy = xmlrpc.client.ServerProxy(_login_uri)

	def __init__(self):
		pass

	def send(self, *args):
		"""
		Sends UDP data to connected socket.
		**Requires `login()` to be called first.**
		"""
		return self.udp.send(b''.join(args))

	def recv(self):
		"""
		Receives UDP data to connected socket.
		**Requires `login()` to be called first.**
		"""
		return self.udp.recv(1024)

	def login(self, first: str, last: str, password: str):
		"""
		Signs into Second Life and establishes a UDP connection with a region.
		"""
		params = {
			'first': first,
			'last': last,
			'passwd': '$1$' + hashlib.md5(password.encode()).hexdigest(),
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
		self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.udp.connect((self.udp_host, self.udp_port))

		# Store/cache some persistent values.
		self.circuit_code       = self.login_response['circuit_code']
		self.circuit_code_bytes = struct.pack('<L', self.circuit_code)
		self.session_id         = self.login_response['session_id']
		self.session_id_bytes   = UUID(self.session_id).bytes
		self.agent_id           = self.login_response['agent_id']
		self.agent_id_bytes     = UUID(self.agent_id).bytes

		return self.login_response
