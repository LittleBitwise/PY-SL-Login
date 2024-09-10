def encode(input: bytes) -> bytes:
	"""
	Zero-bytes are run-length encoded so that up to 255 zeroes become `\\x00\\xff`
	"""
	out = bytearray()
	i, n = 0, len(input)
	while i < n: # While-loop for index skipping.
		if (zeroes := (input[i] == 0x00)):
			while (i + zeroes < n) and input[i + zeroes] == 0x00: zeroes += 1
			out.extend([0x00, zeroes])
			i += zeroes
		else:
			out.append(input[i])
			i += 1
	return bytes(out)

def decode(input: bytes) -> bytes:
	"""
	Converts bytes where zeroes are run-length encoded,
	such that `\\x00\\xff` is unpacked into 255 `\\x00` bytes.
	"""
	out = bytearray()
	i, n = 0, len(input)
	while i < n: # While-loop for index skipping.
		if input[i] == 0x00:
			out.extend(b'\0' * input[i + 1])
			i += 2 # Assumes input was valid.
		else:
			out.append(input[i])
			i += 1
	return bytes(out)

def hex2byte(input: str) -> bytes:
	"""
	Converts formatted string `'AA BB CC DD'` into bytes. Spaces are ignored.
	"""
	return bytes.fromhex(input.replace(' ',''))

def byte2hex(input: bytes) -> str:
	"""
	Converts bytes into formatted string `'AA BB CC DD'`.
	"""
	return ' '.join(f'{byte:02X}' for byte in input)

def byte2id(input: bytes, encoded: bool=False) -> tuple[int, str]:
	"""
	Converts message body into message ID and message frequency.
	**Be sure to pass enough bytes to decode message ID.**
	"""
	if encoded: input = decode(input)
	if    input.startswith(b'\xff\xff\xff'): input = input[:4]
	elif  input.startswith(b'\xff\xff'): input = input[:4]
	elif  input.startswith(b'\xff'): input = input[:2]
	else: input = input[:1]

	id = int.from_bytes(input)

	if   0xFFFFFFFA <= id <= 0xFFFFFFFF: return (id, 'Fixed')
	elif 0xFFFF0001 <= id <= 0xFFFFFFF9: return (id & 0xFFFF, 'Low')
	elif 0x0000FF01 <= id <= 0x0000FFFE: return (id & 0x00FF, 'Medium')
	elif 0x00000001 <= id <= 0x000000FE: return (id & 0x00FF, 'High')
	raise Exception(f'{input} contained invalid message {id} ({hex(id)})')

def debug_zeros():
	def str2bin(s: str) -> str:
		return ' '.join('{0:08b}'.format(c, 'b') for c in s)

	def test(s):
		print('original', s)
		print('encoded ', out := encode(s))
		print('decoded ', out := decode(out))
		print('OK:', s == out)
		print('')

	test('0123 \x00\x00\x00\x00 456'.encode())
	test('\x00\x00\x00\x00'.encode())
	test('\x00\x00\x00\x00\x01'.encode())
	test('\x7f\x00\x7f'.encode())
	test(b'\0' * 255)
	test(bytes.fromhex('FF 00 FF'))

def debug_bytes():
	def test(s):
		print([
			flags := (data := hex2byte(s))[0],
			zer := bool(flags & (zerocode := 0x80)),
			rel := bool(flags & (reliable := 0x40)),
			res := bool(flags & (resended := 0x20)),
			ack := bool(flags & (acknowle := 0x10)),
			byte2id(data[6:12], zer)
		])
	#  Extra header byte ↓  ↓ Packet body (might be zero-encoded)
	#     0  1           5  6
	test('00 00 00 00 12 00 01 01 01 00 00 00')
	test('40 00 00 00 05 00 FF FF 01 42 01 77 9E 1D 56 55 00 4E 22 94 0A CD 7B 5A DD DB E0')
	test('C0 00 00 00 02 00 FF FF 00 01 94 26 82 90 5C 15 08 46 69 64 65 6C 69 73 00 01 02 64 28 B1 50 71 47 2F 9C DB E2 85 CC 39 DA 9E 00 01 CD CC A0 41 00 04 FB FE A8 13 09 AD 3D 92 3A DD 36 DC 7E BB 13 47 9C 43 4A 43 D5 D8 A3 DD B6 24 41 67 82 38 34 78 AB B7 83 E6 3E 93 26 C0 24 8A 24 76 66 85 5D A3 17 9C DA BD 39 8A 9B 6B 13 91 4D C3 33 BA 32 1F BE B1 69 C7 11 EA FF F2 EF E5 0F 24 DC 88 1D F2 CB 1C BC 94 17 46 88 17 AA 35 9E 0A 50 4C 89 FA F3 1A AE 95 84 09 97 94 F7 C8 59 35 13 62 6C 77 DB A2 21 E5 81 35 19 E9 94 7C 03 4F 3E DF A1 C9 DB A2 21 E5 81 35 19 E9 94 7C 03 4F 3E DF A1 C9 00 02 30 41 00 02 A0 41 00 02 A0 41 00 02 A0 41 00 02 A0 41 00 02 0C 42 00 02 0C 42 00 02 0C 42 BD E2 D4 99 11 35 49 9C 82 32 C2 D6 8E 00 01 8C AC B3 03 00 02 01 00 03 0F 61 77 73 2D 75 73 2D 77 65 73 74 2D 32 61 00 01 04 32 32 39 00 01 13 45 73 74 61 74 65 20 2F 20 48 6F 6D 65 73 74 65 61 64 00 01 01 26 82 90 5C 00 04 01 00 07')
