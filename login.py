import logging
import zerocode, packet, template # local

logging.basicConfig(level=logging.DEBUG, format='\t%(levelname)s\t%(message)s\n', filename='dump.log')
log = logging.getLogger()

client = packet.client()
log.info(client.login('firstname', 'lastname', 'password'))

ignored_logging = [
	'LayerData'
	'ObjectUpdate',
	'ObjectUpdateCompressed',
	'ObjectUpdateCached'
	'ImprovedTerseObjectUpdate',
	'AvatarAnimation',
	'CoarseLocationUpdate',
	'PreloadSound',
	'AttachedSound',
	'ScriptControlChange',
]

# Login preamble.

client.send(
	packet.header(template.message['UseCircuitCode'], client.sequence),
	client.circuit_code_bytes,
	client.session_id_bytes,
	client.agent_id_bytes,
)

client.send(
	packet.header(template.message['CompleteAgentMovement'], client.sequence),
	client.agent_id_bytes,
	client.session_id_bytes,
	client.circuit_code_bytes,
)

# Main connection loop.

while data := client.receive():
	number = packet.message(data)
	message = template.message[number]

	if message not in ignored_logging:
		log.debug(f'{packet.human_header(data)}\t{message}\n\tUDP: {zerocode.byte2hex(data)}')

	if message == 'RegionHandshake':
		client.send(
			packet.header(template.message['RegionHandshakeReply'], client.sequence, packet.ZEROCODED),
			zerocode.encode_all(
				client.agent_id_bytes,
				client.session_id_bytes,
				packet.u32.zero
			),
		)
		client.send(
			packet.header(template.message['AgentUpdate'], client.sequence, packet.ZEROCODED),
			zerocode.encode_all(
				client.agent_id_bytes,
				client.session_id_bytes,
				b'\x00' * 106,
			)
		)

	if message == 'StartPingCheck':
		pingID, _ = packet.unpack_sequence(data[7:12], 'b', '<i')
		client.send(
			packet.header(template.message['CompletePingCheck'], client.sequence),
			packet.pack_sequence(
				packet.u8, pingID
			)
		)

	if packet.is_reliable(data):
		message_number = packet.sequence(data)
		client.send(
			packet.header(template.message['PacketAck'], client.sequence),
			packet.pack_sequence(
				packet.u8, 1,
				packet.u32, message_number,
			)
		)

	if message == 'KickUser':
		data = packet.unpack_sequence(
			data[48:],
			packet.u16.format,
			packet.string.format
		)
		reason = packet.string.from_bytes(data[-1])
		log.warning(f'Disconnected: {reason}')
		break
