import logging
import struct # UDP communication
import zerocode, packet # local

logging.basicConfig(level=logging.DEBUG, format='\t%(levelname)s\t%(message)s\n', filename='dump.log')
log = logging.getLogger()

client = packet.client()
log.info(client.login('firstname', 'lastname', 'password'))

# Login preamble.

log.debug('UseCircuitCode')
client.send(
	packet.header(packet.UseCircuitCode, client.sequence),
	client.circuit_code_bytes,
	client.session_id_bytes,
	client.agent_id_bytes,
)

log.debug('CompleteAgentMovement')
client.send(
	packet.header(packet.CompleteAgentMovement, client.sequence),
	client.agent_id_bytes,
	client.session_id_bytes,
	client.circuit_code_bytes,
)

# Main connection loop.

while data := client.recv():
	(mID, mHZ) = packet.message_from_body(data[packet.BODY_BYTE:], packet.is_zerocoded(data))

	if (mID, mHZ) not in [(6, 'Medium'), (13, 'Medium'), (15, 'Medium'), (189, 'Low')]:
		log.debug(f'{packet.human_header(data)}\n\tUDP: {zerocode.byte2hex(data)}')

	if (mID, mHZ) == (148, 'Low'):
		log.debug('RegionHandshakeReply')
		client.send(
			packet.header(packet.RegionHandshakeReply, client.sequence),
			zerocode.encode_all(
				client.agent_id_bytes,
				client.session_id_bytes
			),
		)
		log.debug('AgentUpdate')
		client.send(
			packet.header(packet.AgentUpdate, client.sequence, packet.ZEROCODED),
			client.agent_id_bytes,
			client.session_id_bytes,
			packet.zero_rot_bytes, # BodyRotation
			packet.zero_rot_bytes, # HeadRotation
			packet.zero_1_bytes, # State
			packet.zero_vec_bytes, # CameraCenter
			packet.zero_vec_bytes, # CameraAtAxis
			packet.zero_vec_bytes, # CameraLeftAxis
			packet.zero_vec_bytes, # CameraUpAxis
			packet.zero_f_bytes, # Far
			packet.zero_4_bytes, # ControlFlags
			packet.zero_1_bytes, # Flags
		)
		pass

	if (mID, mHZ) == (1, 'High'):
		pingID, _ = packet.unpack_sequence(data[7:12], 'b', '<i')
		client.send(
			packet.header(packet.CompletePingCheck, client.sequence),
			bytes([pingID])
		)
		continue

	if packet.is_reliable(data):
		message_number = packet.sequence_from_header(data)
		client.send(
			packet.header(packet.PacketAck, client.sequence),
			packet.pack_sequence(
				packet.u08, 1,
				packet.u32, message_number,
			)
		)
		continue

log.debug('UDP connection closed, no data received.')
