def parse():
	"""
	Parses `message_template.msg` and returns a bidirectional dictionary for message names and their encoded number and frequency.
	"""
	out = {}

	conversion = {
        'Low':    lambda x: 0xffff0000 | x,
        'Medium': lambda x: (0xff00 | x) << 16,
        'High':   lambda x: x << 24,
        'Fixed':  lambda x: x,
    }

	with open('message_template.msg', 'r') as file:
		for line in map(str.strip, file):
			if line.startswith('//') or line.startswith('{') or not line:
				continue

			word = line.split()

			if len(word) < 3:
				continue

			name, type, freq = word[0], word[1], word[2]
			if type not in conversion.keys():
				continue

			number = int(freq if type != 'Fixed' else int(freq, 16))
			number = conversion[type](number)

			out[number] = name
			out[name] = number
	return out

message = parse()

if __name__ == '__main__':
	to_hex = lambda x: hex(x)[2:]
	print('Fixed',  k := 'PacketAck', to_hex(message[k]))
	print('High',   k := 'AgentUpdate', to_hex(message[k]))
	print('High',   k := 'StartPingCheck', to_hex(message[k]))
	print('High',   k := 'CompletePingCheck', to_hex(message[k]))
	print('High',   k := 'LayerData', to_hex(message[k]))
	print('Medium', k := 'CoarseLocationUpdate', to_hex(message[k]))
	print('Low',    k := 'UseCircuitCode', to_hex(message[k]))
	print('Low',    k := 'CompleteAgentMovement', to_hex(message[k]))
	print('Low',    k := 'RegionHandshake', to_hex(message[k]))
	print('Low',    k := 'RegionHandshakeReply', to_hex(message[k]))
	print('Low',    k := 'KickUser', to_hex(message[k]))
