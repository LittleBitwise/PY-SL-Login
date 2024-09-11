import xmlrpc.client, socket, struct, hashlib
from uuid import UUID

# Common constants
zero_rot_bytes = struct.pack('<ffff', 0.0, 0.0, 0.0, 0.0)
zero_vec_bytes = struct.pack('<fff', 0.0, 0.0, 0.0)
zero_f_bytes = struct.pack('<f', 0.0)
zero_4_bytes = struct.pack('>L', 0)
zero_1_bytes = struct.pack('>B', 0)

# Utility functions
def header(message: int, sequence: int, flags=0, extra_byte=0, extra_header=None):
	out = bytearray(struct.pack('>BLB', flags, sequence, extra_byte))
	if extra_header is not None:
		if extra_byte != len(header := bytes(extra_header)):
			raise Exception('Extra byte does not match extra header size.')
		out.extend(header)
	out.extend(struct.pack('>L', message))
	return bytes(out)

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
