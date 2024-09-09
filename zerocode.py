# 0's are run-length encoded, such that
# series of 1 to 255 zero-bytes are encoded into 2 bytes.
# Example: '\x00\xff'
#           ^^^^-- null-byte (zero)
#               ^^^^-- count (255)

def encode(input: bytes) -> bytes:
	out = bytearray()
	i, n = 0, len(input)
	while i < n: # While-loop for index skipping.
		match _ := input[i]:
			case 0x00:
				# Look ahead from current index.
				# Find next nonzero byte.
				# Use that index as length.
				v = memoryview(input[i:]); v_len = len(v)
				zeroes = next((x for x, byte in enumerate(v) if byte != 0x00), v_len)
				out.extend([0x00, zeroes])
				i += zeroes
			case byte:
				out.append(byte)
				i += 1
	return bytes(out)

def decode(input: bytes) -> bytes:
	out = bytearray()
	i, n = 0, len(input)
	while i < n: # While-loop for index skipping.
		match _ := input[i]:
			case 0x00:
				out.extend(b'\0' * input[i + 1])
				i += 2
			case byte:
				out.append(byte)
				i += 1
	return bytes(out)

def debug():
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
