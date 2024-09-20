import logging
import threading # for user input
import zerocode, packet, template # local

logging.basicConfig(level=logging.DEBUG, format='\t%(levelname)s\t%(message)s\n', filename='dump.log')
log = logging.getLogger()

ignored_logging = [
	'LayerData',
	'SimulatorViewerTimeMessage',
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

# User input handler.

user_input = None

def UserInputThread():
	global user_input
	while True:
		user_input = input()
def HandleUserInput():
	global user_input
	if user_input.lower() == 'q':
		exit()
	SendChatFromViewer(user_input)
	user_input = None
	pass

user_input_thread = threading.Thread(
	name='user_input_thread',
	target=UserInputThread,
	daemon=True
)
user_input_thread.start()

# UDP messages.

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
def SendChatFromViewer(text: str):
	log.info(f'Sending chat: {text}')
	text_bytes = text.encode('utf-8')
	client.send(
		packet.header(template.message['ChatFromViewer'], client.sequence, packet.ZEROCODED),
		zerocode.encode(
			packet.pack_sequence(
				packet.uuid, client.agent_id_bytes,
				packet.uuid, client.session_id_bytes,
				packet.variable2, len(text_bytes),
				packet.string, text_bytes,
				packet.u8, 1,
				packet.u32, 0
			)
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
	number = packet.message_number(data)
	message = template.message[number]

	if message not in ignored_logging:
		log.debug('%s\t%s\n\tUDP: %s', packet.human_header(data), message, zerocode.byte2hex(data))

	if packet.is_reliable(data):
		sequence_number = packet.sequence_number(data)
		SendPacketAck(sequence_number)

	if message == 'StartPingCheck':
		[pingID] = packet.unpack_sequence(data[7:8], packet.u8)
		SendCompletePingCheck(pingID)

	if message == 'RegionHandshake':
		SendRegionHandshakeReply()
		SendAgentUpdate()

	if message == 'KickUser':
		HandleKickUser(data)
		break

	if user_input:
		HandleUserInput()
