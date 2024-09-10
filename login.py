import hashlib, xmlrpc.client, logging # absolute minimum
import struct, socket, uuid # UDP communication
import zerocode # local

logging.basicConfig(level=logging.DEBUG, format='\n\t%(levelname)s\t%(message)s\n')
log = logging.getLogger()

def login(first: str, last: str, password: str):
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

	log.debug(params)

	uri = 'https://login.agni.lindenlab.com/cgi-bin/login.cgi'
	proxy = xmlrpc.client.ServerProxy(uri)
	return proxy.login_to_simulator(params)

result = login('first', 'last', 'password')

log.info(result)

sim_ip = result['sim_ip']
sim_port = result['sim_port']
circuit_code = result['circuit_code']
session_id = result['session_id']
agent_id = result['agent_id']

agent_id_bytes = uuid.UUID(agent_id).bytes
session_id_bytes = uuid.UUID(session_id).bytes
circuit_code_bytes = struct.pack('<L', circuit_code)
zero_rot_bytes = struct.pack('<ffff', 0.0, 0.0, 0.0, 0.0)
zero_vec_bytes = struct.pack('<fff', 0.0, 0.0, 0.0)
zero_f_bytes = struct.pack('<f', 0.0)
zero_4_bytes = struct.pack('>L', 0)
zero_1_bytes = struct.pack('>B', 0)

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.connect((sim_ip, sim_port))

def packet_header(message: int, sequence: int, flags=0, extra_byte=0, extra_header=None):
	out = bytearray(struct.pack('>BLB', flags, sequence, extra_byte))
	if extra_header is not None:
		if extra_byte != len(header := bytes(extra_header)):
			raise Exception('Extra byte does not match extra header size.')
		out.extend(header)
	out.extend(struct.pack('>L', message))
	return bytes(out)

def message(*args) -> bytes:
	return b''.join(args)

# Login preamble.

log.debug('UseCircuitCode')
udp.send(message(
	packet_header(0xffff0003, 1),
	circuit_code_bytes,
	session_id_bytes,
	agent_id_bytes,
))

log.debug('CompleteAgentMovement')
udp.send(message(
	packet_header(0xffff00f9, 2),
	agent_id_bytes,
	session_id_bytes,
	circuit_code_bytes,
))

log.debug('UUIDNameRequest')
udp.send(message(
	packet_header(0xffff00eb, 4),
	agent_id_bytes,
))

# Main connection loop.

sequence = 5
while data := udp.recv(udp_buffer := 1024):
	log.debug(f'{zerocode.packet2human(data[0:12])}\n\tUDP: {zerocode.byte2hex(data)}')

	if zerocode.reliable(data):
		message_number = int.from_bytes(data[1:5])
		log.debug(f'ACK {message_number}')
		sequence += 1
		udp.send(message(
			packet_header(0xfffffffb, sequence),
			struct.pack('>B', 1),
			struct.pack('<L', message_number),
		))
		continue

	(mID, mHZ) = zerocode.byte2id(data[6:12])

	if (mID, mHZ) == (148, 'Low'): # RegionHandshake
		log.debug('RegionHandshakeReply')
		sequence += 1
		udp.send(message(
			packet_header(0xffff0095, sequence),
			zerocode.encode(message(agent_id_bytes, session_id_bytes)),
		))

		log.debug('AgentUpdate')
		sequence += 1
		udp.send(message(
			packet_header(0x04, 3),
			agent_id_bytes,
			session_id_bytes,
			zero_rot_bytes,
			zero_rot_bytes,
			zero_1_bytes, # state
			zero_vec_bytes,
			zero_vec_bytes,
			zero_vec_bytes,
			zero_vec_bytes,
			zero_f_bytes,
			zero_4_bytes, # inputs
			zero_1_bytes, # flags
		))
		break
	pass

log.debug('UDP connection closed, no data received.')
