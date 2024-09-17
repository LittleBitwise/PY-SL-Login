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

def encode_all(*args: bytes) -> bytes:
	"""
	Calls `packet.encode()` on each argument containing `bytes`.
	"""
	return bytes(bytearray().join(encode(arg) for arg in args if isinstance(arg, bytes)))

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

