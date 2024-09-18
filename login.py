import logging
import zerocode, packet, template # local

logging.basicConfig(level=logging.DEBUG, format='\t%(levelname)s\t%(message)s\n', filename='dump.log')
log = logging.getLogger()

ignored_logging = [
	'LayerData',
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

client = packet.client()
log.info(client.login('firstname', 'lastname', 'password'))

log.info('LOGGED IN')

# UDP messages

def SendUseCircuitCode():
	client.send(
		packet.header(template.message['UseCircuitCode'], client.sequence),
		client.circuit_code_bytes,
		client.session_id_bytes,
		client.agent_id_bytes,
	)
def SendCompleteAgentMovement():
	client.send(
		packet.header(template.message['CompleteAgentMovement'], client.sequence),
		client.agent_id_bytes,
		client.session_id_bytes,
		client.circuit_code_bytes,
	)
def SendRegionHandshakeReply():
	client.send(
		packet.header(template.message['RegionHandshakeReply'], client.sequence, packet.ZEROCODED),
		zerocode.encode_all(
			client.agent_id_bytes,
			client.session_id_bytes,
			packet.u32.zero
		),
	)
def SendAgentUpdate():
	client.send(
		packet.header(template.message['AgentUpdate'], client.sequence, packet.ZEROCODED),
		zerocode.encode_all(
			client.agent_id_bytes,
			client.session_id_bytes,
			b'\x00' * 106,
		)
	)
def SendCompletePingCheck(pingID: int):
	client.send(
		packet.header(template.message['CompletePingCheck'], client.sequence),
		packet.pack_sequence(
			packet.u8, pingID
		)
	)
def SendPacketAck(message_number: int):
	client.send(
		packet.header(template.message['PacketAck'], client.sequence),
		packet.pack_sequence(
			packet.u8, 1,
			packet.u32, message_number,
		)
	)
def HandleKickUser(data: bytes):
	data = packet.unpack_sequence(
		data[48:],
		packet.u16.format,
		packet.string.format
	)
	reason = packet.string.from_bytes(data[-1])
	log.warning(f'Disconnected: {reason}')

# Login preamble.

SendUseCircuitCode()
SendCompleteAgentMovement()

# Main connection loop.

while data := client.receive():
	number = packet.message(data)
	message = template.message[number]

	if message not in ignored_logging:
		log.debug('%s\t%s\n\tUDP: %s', packet.human_header(data), message, zerocode.byte2hex(data))

	if message == 'RegionHandshake':
		SendRegionHandshakeReply()
		SendAgentUpdate()

	if message == 'StartPingCheck':
		pingID, _ = packet.unpack_sequence(data[7:12], 'b', '<i')
		SendCompletePingCheck(pingID)

	if packet.is_reliable(data):
		message_number = packet.sequence(data)
		SendPacketAck(message_number)

	if message == 'KickUser':
		HandleKickUser(data)
		break
