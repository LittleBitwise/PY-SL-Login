# 0's are run-length encoded, such that
# series of 1 to 255 zero-bytes are encoded into 2 bytes.
# Example: '\x00\xff'
#           ^^^^-- null-byte (zero)
#               ^^^^-- count (255)

def encode(input: bytes) -> bytes:
	out = ''
	i, n = 0, len(input)
	while i < n: # While-loop for next-byte access.
		match _ := input[i]:
			case 0x00:
				# Look ahead from current index.
				# Find next nonzero byte.
				# Use index as length.
				v = memoryview(input[i:]);
				zeroes = next((x for x, byte in enumerate(v) if byte != 0x00), len(v))
				out += '\0' + chr(zeroes)
				i += zeroes
			case b:
				out += chr(b)
				i += 1
	return bytes(out, encoding='ASCII')

def decode(input: bytes) -> bytes:
	out = ''
	i, n = 0, len(input)
	while i < n: # While-loop for next-byte access.
		match _ := input[i]:
			case 0x00:
				out += '\0' * input[i + 1]
				i += 2
			case byte:
				out += chr(byte)
				i += 1
	return bytes(out, encoding='ASCII')

# For testing
def str2bin(s: str) -> str:
	return ' '.join('{0:08b}'.format(c, 'b') for c in s)

def debug():
	def test(s):
		print('original', s)
		print('encoded ', out := encode(s))
		print('decoded ', out := decode(out))
		print('OK:', s == out)
		print('')

	test('0123 \x00\x00\x00\x00 456'.encode())
	test('\x00\x00\x00\x00'.encode())
	test('\x00\x00\x00\x00\x01'.encode())
