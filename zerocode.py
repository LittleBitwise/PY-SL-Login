# 0's in packet body are run-length encoded,
# such that series of 1-255 zero bytes are encoded to take 2 bytes.
# Example: '\x00\xff'
#           ^^^^-- null-byte (zero)
#               ^^^^-- count (255)

def encode(input: bytes):
	out = ''
	in_zero = False
	zeroes = 0
	for byte in input:
		match byte:
			case 0x00 if in_zero == False:
				in_zero = True
				out += chr(0)
				zeroes = 1
				continue
			case 0x00:
				zeroes += 1
			case b if in_zero == True:
				in_zero = False
				out += chr(zeroes)
				out += chr(b)
				zeroes = 0
			case b:
				out += chr(b)
	if zeroes != 0:
		out += chr(zeroes)
		zeroes = 0
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
	# test = bytes.fromhex('B9 00 00 EF FF') # b'\xb9\x00\x00\xef\xff'
	test = '0123 \x00\x00\x00\x00 456'.encode()
	test = '\x00\x00\x00\x00'.encode()
	print('original', test)

	out = encode(test)
	print('encoded ', out)

	out = decode(out)
	print('decoded ', out)
