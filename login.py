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

def udp_agent_update(seq):
	data_header = struct.pack('>BLB', 0x00, seq, 0x00)
	packed_data_message_ID = struct.pack('>B', 0x04)
	packed_data_ID = agent_id_bytes + session_id_bytes
	packed_data_QuatRots = zero_rot_bytes + zero_rot_bytes
	packed_data_State = struct.pack('<B', 0x00)
	packed_data_Camera = zero_vec_bytes + zero_vec_bytes + zero_vec_bytes + zero_vec_bytes
	packed_data_Flags = struct.pack('<fLB', 0.0,0x00,0x00)

	byte_sequence = [
		packed_data_message_ID,
		packed_data_ID,
		packed_data_QuatRots,
		packed_data_State,
		packed_data_Camera,
		packed_data_Flags,
	]

	packed_data = data_header + zerocode.encode(b''.join(byte_sequence)).encode()
	udp.sendto(packed_data, (sim_ip, sim_port))

result = login('first', 'last', 'password')

log.info(result)

sim_ip = result['sim_ip']
sim_port = result['sim_port']
circuit_code = result['circuit_code']
session_id = result['session_id']
agent_id = result['agent_id']

agent_id_bytes = uuid.UUID(agent_id).bytes
session_id_bytes = uuid.UUID(session_id).bytes
zero_rot_bytes = struct.pack('<ffff', 0.0, 0.0, 0.0, 0.0)
zero_vec_bytes = struct.pack('<fff', 0.0, 0.0, 0.0)

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

log.debug('UseCircuitCode')
data = struct.pack('>BLBL', 0x00, 1, 0x00, 0xffff0003) + struct.pack('<L', circuit_code) + session_id_bytes + agent_id_bytes
udp.sendto(data, (sim_ip, sim_port))

log.debug('CompleteAgentMovement')
data = struct.pack('>BLBL', 0x00, 2, 0x00, 0xffff00f9) + agent_id_bytes + session_id_bytes + struct.pack('<L', circuit_code)
udp.sendto(data, (sim_ip, sim_port))

log.debug('AgentUpdate')
udp_agent_update(3)

log.debug('UUIDNameRequest')
fix_ID = int('ffff0000', 16) + 235
data_header = struct.pack('>BLB', 0x00, 4, 0x00)
packed_data = agent_id_bytes
packed_data += struct.pack('L', fix_ID) + struct.pack('>B',len(agent_id)) + packed_data
udp.sendto(data, (sim_ip, sim_port))

log.debug('Finished!')
