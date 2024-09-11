import logging
import struct # UDP communication
import zerocode, packet # local

logging.basicConfig(level=logging.DEBUG, format='\n\t%(levelname)s\t%(message)s\n', filename='dump.log')
log = logging.getLogger()

client = packet.client()
log.info(client.login('firstname', 'lastname', 'password'))

# Login preamble.

log.debug('UseCircuitCode')
client.send(
	packet.header(0xffff0003, 1),
	client.circuit_code_bytes,
	client.session_id_bytes,
	client.agent_id_bytes,
)

log.debug('CompleteAgentMovement')
client.send(
	packet.header(0xffff00f9, 2),
	client.agent_id_bytes,
	client.session_id_bytes,
	client.circuit_code_bytes,
)

log.debug('UUIDNameRequest')
client.send(
	packet.header(0xffff00eb, 4),
	client.agent_id_bytes,
)

# Main connection loop.

sequence = 5
while data := client.recv():
	log.debug(f'{zerocode.packet2human(data[0:12])}\n\tUDP: {zerocode.byte2hex(data)}')

	if zerocode.reliable(data):
		message_number = int.from_bytes(data[1:5])
		log.debug(f'ACK {message_number}')
		sequence += 1
		client.send(
			packet.header(0xfffffffb, sequence),
			struct.pack('>B', 1),
			struct.pack('<L', message_number),
		)
		continue

	(mID, mHZ) = zerocode.byte2id(data[6:12])

	if (mID, mHZ) == (148, 'Low'): # RegionHandshake
		log.debug('RegionHandshakeReply')
		sequence += 1
		client.send(
			packet.header(0xffff0095, sequence),
			zerocode.encode_all(client.agent_id_bytes, client.session_id_bytes),
		)

		log.debug('AgentUpdate')
		sequence += 1
		client.send(
			packet.header(0x04, 3),
			client.agent_id_bytes,
			client.session_id_bytes,
			packet.zero_rot_bytes,
			packet.zero_rot_bytes,
			packet.zero_1_bytes, # state
			packet.zero_vec_bytes,
			packet.zero_vec_bytes,
			packet.zero_vec_bytes,
			packet.zero_vec_bytes,
			packet.zero_f_bytes,
			packet.zero_4_bytes, # inputs
			packet.zero_1_bytes, # flags
		)
		break
	pass

log.debug('UDP connection closed, no data received.')
