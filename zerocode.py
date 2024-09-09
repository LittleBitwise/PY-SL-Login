# 0's are run-length encoded, such that
# series of 1 to 255 zero-bytes are encoded into 2 bytes.
# Example: '\x00\xff'
#           ^^^^-- null-byte (zero)
#               ^^^^-- count (255)

def encode(input: bytes) -> bytes:
	out = bytearray()
	i, n = 0, len(input)
	while i < n: # While-loop for index skipping.
		if input[i] == 0x00:
			# Look ahead from current index.
			# Find first nonzero byte.
			# Use that index as length.
			zeroes = 1
			while (i + zeroes < n) and input[i + zeroes] == 0x00:
				zeroes += 1;
			out.extend([0x00, zeroes])
			i += zeroes
		else:
			out.append(input[i])
			i += 1
	return bytes(out)

def decode(input: bytes) -> bytes:
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
