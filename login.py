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

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def packet_header(message: int, sequence: int, flags=0, extra_byte=0, extra_header=None):
	out = bytearray(struct.pack('>BLB', flags, sequence, extra_byte))
	if extra_header is not None:
		if extra_byte == len(header := bytes(extra_header)):
			out.append(header)
		else:
			raise Exception('Extra byte does not match extra header size.')
	out.extend(struct.pack('>L', message))
	return bytes(out)

def message(*args) -> bytes:
	return b''.join(args)

log.debug('UseCircuitCode')
udp.sendto(message(
	packet_header(0xffff0003, 1),
	circuit_code_bytes,
	session_id_bytes,
	agent_id_bytes,
), (sim_ip, sim_port))

log.debug('CompleteAgentMovement')
udp.sendto(message(
	packet_header(0xffff00f9, 2),
	agent_id_bytes,
	session_id_bytes,
	circuit_code_bytes,
), (sim_ip, sim_port))

log.debug('AgentUpdate')
udp.sendto(message(
	packet_header(0x04, 3),
	agent_id_bytes,
	session_id_bytes,
	zero_rot_bytes,
	zero_rot_bytes,
	bytes(0), # state
	zero_vec_bytes,
	zero_vec_bytes,
	zero_vec_bytes,
	zero_vec_bytes,
	zero_f_bytes,
	bytes(0), # inputs
	bytes(0), # flags
), (sim_ip, sim_port))

log.debug('UUIDNameRequest')
udp.sendto(message(
	packet_header(0xffff00EB, 4),
	agent_id_bytes,
), (sim_ip, sim_port))

log.debug('Finished!')

# todo
# INCOMING RegionHandshake
# RegionHandshakeReply
# AgentThrottle ?
# AgentFOV ?
# AgentHeightWidth ?
