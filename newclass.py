from uuid import UUID
from pprint import pformat as pretty
from typing import Self
import struct
import zerocode, packet, template

class Format:
	zero = b''
	format = ''
	def __init__(self, value):
		self._data = value[0] if isinstance(value, tuple) else value
	def __str__(self): return f'{self.format}'
	def __repr__(self): return f'{pretty(self._data)}'


	@property
	def value(self):
		return self._data

	def alias(alias: str) -> Self:
		return {
			'Fixed': U32,
			'Low': U32,
			'Medium': U16,
			'High': U8
		}[alias]

class U8(Format):  format = '<B'; size = 1; zero = b'\x00' * size
class S8(Format):  format = '<b'; size = 1; zero = b'\x00' * size
class U16(Format): format = '<H'; size = 2; zero = b'\x00' * size
class S16(Format): format = '<h'; size = 2; zero = b'\x00' * size
class U32(Format): format = '<I'; size = 4; zero = b'\x00' * size
class S32(Format): format = '<i'; size = 4; zero = b'\x00' * size
class F32(Format): format = '<f'; size = 4; zero = b'\x00' * size
class U64(Format): format = '<q'; size = 8; zero = b'\x00' * size
class S64(Format): format = '<Q'; size = 8; zero = b'\x00' * size
class F64(Format): format = '<d'; size = 8; zero = b'\x00' * size
class Bool(U8): pass # Boolean values identical to U8

class Vector(Format):
	format = '<fff'
	zero = (0.0, 0.0, 0.0)
	def __init__(self, value):
		expect = 3
		if expect != (length := len(value)):
			raise ValueError(f'Expected {expect} values, got {length}')
		self._data = value

class Rotation(Format):
	format = '<ffff';
	zero = (0.0, 0.0, 0.0, 0.0)
	def __init__(self, value):
		expect = 4
		if expect != (length := len(value)):
			raise ValueError(f'Expected {expect} values, got {length}')
		self._data = value

class Uuid(Format):
	format = '16s';
	zero = UUID(int=0).bytes
	def __init__(self, value: str|None=None):
		if isinstance(value, str):
			self._data = UUID(hex=value).bytes
		elif isinstance(value, bytes):
			self._data = UUID(bytes=value).bytes
		else:
			self._data = self.zero
	def __repr__(self) -> str:
		return str(UUID(bytes=self._data))
	@property
	def text(self):
		return str(UUID(bytes=self._data))

class Variable1(Format):
	format = '<B*s';
	zero = b'\x00'
	def __init__(self, value):
		if len(value) != 2:
			raise ValueError(f'Expected 2 values, got {len(value)}')
		self._data = value
	def __repr__(self) -> str:
		if isinstance(self._data[1], bytes):
			s = str(self._data[1], 'utf-8', 'replace')
		else:
			s = self._data[1]
		return f'[{self._data[0]}] {s}'
	@property
	def length(self):
		return self._data[0]
	@property
	def text(self):
		return self._data[1]

class Variable2(Variable1):
	format = '<H*s';

class Message:
	_zerocoded = False
	_frequency = Format.alias('Low').size
	_keys = {}

	def __init__(self):
		self._data = dict.fromkeys(self._keys)

	def __getitem__(self, key):
		if key not in self._keys:
			raise KeyError(f"Key '{key}' not in {', '.join(self._keys)}")
		# print(f'Get self._data["{key}"] =', self._data[key].value)
		return self._data[key].value

	def __setitem__(self, key, value):
		if key not in self._keys:
			raise KeyError(f"Key `{key}` not in {', '.join(self._keys)}")
		expected = self._keys[key]
		if not isinstance(value, expected):
			raise ValueError(f"{key} value `{value}` is not {expected}")
		self._data[key] = value
		# print(f'Set self._data["{key}"] =', value.value)

	def __repr__(self):
		return pretty(self._data, sort_dicts=False)

class StartPingCheck(Message):
	_frequency = Format.alias('High').size
	_keys = {
		'PingID': U8,
		'OldestUnacked': U32,
	}

class AgentMovementComplete(Message):
	_keys = {
		'AgentID': Uuid,
		'SessionID': Uuid,
		'Position': Vector,
		'LookAt': Vector,
		'RegionHandle': U64,
		'Timestamp': U32,
		'ChannelVersion': Variable2,
	}

class ChatFromSimulator(Message):
	_keys = {
		'FromName': Variable1,
		'SourceID': Uuid,
		'OwnerID': Uuid,
		'SourceType': U8,
		'ChatType': U8,
		'Audible': U8,
		'Position': Vector,
		'Message': Variable2,
	}

class ImprovedInstantMessage(Message):
	_zerocoded = True
	_keys = {
		'AgentID': Uuid,
		'SessionID': Uuid,
		'FromGroup': Bool,
		'ToAgentID': Uuid,
		'ParentEstateID': U32,
		'RegionID': Uuid,
		'Position': Vector,
		'Offline': U8,
		'Dialog': U8,
		'ID': Uuid,
		'Timestamp': U32,
		'FromAgentName': Variable1,
		'Message': Variable2,
		'BinaryBucket': Variable2,
	}

class RegionHandshake(Message):
	_zerocoded = True
	_keys = {
		'RegionFlags': U32,
		'SimAccess': U8,
		'SimName': Variable1,
		'SimOwner': Uuid,
		'IsEstateManager': Bool,
		'WaterHeight': F32,
		'BillableFactor': F32,
		'CacheID': Uuid,
		'TerrainBase0': Uuid,
		'TerrainBase1': Uuid,
		'TerrainBase2': Uuid,
		'TerrainBase3': Uuid,
		'TerrainDetail0': Uuid,
		'TerrainDetail1': Uuid,
		'TerrainDetail2': Uuid,
		'TerrainDetail3': Uuid,
		'TerrainStartHeight00': F32,
		'TerrainStartHeight01': F32,
		'TerrainStartHeight10': F32,
		'TerrainStartHeight11': F32,
		'TerrainHeightRange00': F32,
		'TerrainHeightRange01': F32,
		'TerrainHeightRange10': F32,
		'TerrainHeightRange11': F32,
	}

@classmethod
def _from_bytes(cls, data: bytes):
	"""Parses packet bytes according to message fields."""
	def unpack_sequence(buffer: bytes, *args):
		"""Unpacks bytes from buffer according to struct format strings"""
		out = []
		offset = 0
		last_val = None
		for format in map(str, args):
			# print(f'FORMAT {format:<4}', 'AHEAD', zerocode.byte2hex(buffer[offset:offset+4]), 'OFFSET', offset)
			if format == Variable1.format:
				[length] = struct.unpack_from(U8.format, buffer, offset)
				# print('VAR1 LENGTH', str(length))
				[string] = struct.unpack_from(f'{str(length)}s', buffer, offset + 1)
				out.append((length, string))
				last_val = None
				offset += 1 + length
				continue
			if format == Variable2.format:
				[length] = struct.unpack_from(U16.format, buffer, offset)
				# print('VAR2 LENGTH', str(length))
				[string] = struct.unpack_from(f'{str(length)}s', buffer, offset + 2)
				out.append((length, string))
				last_val = None
				offset += 2 + length
				continue
			if '*' in format and last_val is not None:
				format = format.replace('*', str(last_val))
			if format == '0s':
				out.append(b'')
				last_val = None
				continue
			values = struct.unpack_from(format, buffer, offset)
			single = len(values) == 1
			out.append(values[0] if single else values)
			last_val = values[0] if single else None
			offset += struct.calcsize(format)
		return out
	message = cls()
	body_byte = 6
	# print('CLASS', type(message), 'IN', __class__)
	# print('KEYS', message._keys)
	# print('VALUES', message._keys.values())
	formats = [x.format for x in message._keys.values()]
	# print('FORMATS', formats)
	if message._zerocoded:
		data = data[body_byte:]
		data = zerocode.decode(data)
		# print(zerocode.byte2hex(data))
		data = data[message._frequency:]
		unpacked = unpack_sequence(data, *formats)
	else:
		data = data[body_byte + message._frequency:]
		# print(zerocode.byte2hex(data))
		unpacked = unpack_sequence(data, *formats)

	# print('UNPACKED', unpacked)
	for i, (name, impl) in enumerate(message._keys.items()): # assign
		# print('ASSIGN', name, unpacked[i], impl, '->', impl(unpacked[i]))
		message[name] = impl(unpacked[i])
	return message

def _to_bytes(self):
	out = bytearray()

	# for i, (name, impl) in enumerate(self._keys.items()):
	for (name, impl) in self._keys.items():
		value = self[name] # raw data
		# print('CONVERTING', name, impl, value, type(value))

		if isinstance(value, int):
			value = struct.pack(impl.format, value)
		elif isinstance(value, float):
			value = struct.pack(F32.format, value)
		elif isinstance(value, tuple):
			if 2 == (_len := len(value)): # Variable1, Variable2
				_length_format = impl.format[:2]
				out.extend(struct.pack(_length_format, value[0]))
				out.extend(value[1])
				# print('BYTESTRING', zerocode.encode(out).hex(' '), '\n')
				continue
			elif 3 == _len: value = struct.pack(Vector.format, *value)
			elif 4 == _len: value = struct.pack(Rotation.format, *value)
			else: raise ValueError(f'Unexpected tuple length: {_len}')

		# print('\t', type(value))
		out.extend(value)
		# print('BYTESTRING', zerocode.encode(out).hex(' '), '\n')

	if self._zerocoded:
		out = zerocode.encode(out)
	return bytes(out)

Message.to_bytes = _to_bytes
Message.from_bytes = _from_bytes

# StartPingCheck
data = zerocode.hex2byte('00 00 00 00 38 00 01 01 37 00 00 00')
print(StartPingCheck.from_bytes(data))
print()

# ChatFromSimulator "test"
data = zerocode.hex2byte('40 00 00 00 33 00 FF FF 00 8B 12 57 75 6C 66 69 65 20 52 65 61 6E 69 6D 61 74 6F 72 00 77 9E 1D 56 55 00 4E 22 94 0A CD 7B 5A DD DB E0 77 9E 1D 56 55 00 4E 22 94 0A CD 7B 5A DD DB E0 01 01 01 2A B0 E3 42 F3 15 A6 41 FD 8B BC 41 05 00 74 65 73 74 00')
print(ChatFromSimulator.from_bytes(data))
print()

# RegionHandshake
data = zerocode.hex2byte('C0 00 00 00 02 00 FF FF 00 01 94 26 82 90 5C 15 08 46 69 64 65 6C 69 73 00 01 02 64 28 B1 50 71 47 2F 9C DB E2 85 CC 39 DA 9E 00 01 CD CC A0 41 00 04 FB FE A8 13 09 AD 3D 92 3A DD 36 DC 7E BB 13 47 9C 43 4A 43 D5 D8 A3 DD B6 24 41 67 82 38 34 78 AB B7 83 E6 3E 93 26 C0 24 8A 24 76 66 85 5D A3 17 9C DA BD 39 8A 9B 6B 13 91 4D C3 33 BA 32 1F BE B1 69 C7 11 EA FF F2 EF E5 0F 24 DC 88 1D F2 CB 1C BC 94 17 46 88 17 AA 35 9E 0A 50 4C 89 FA F3 1A AE 95 84 09 97 94 F7 C8 59 35 13 62 6C 77 DB A2 21 E5 81 35 19 E9 94 7C 03 4F 3E DF A1 C9 DB A2 21 E5 81 35 19 E9 94 7C 03 4F 3E DF A1 C9 00 02 30 41 00 02 A0 41 00 02 A0 41 00 02 A0 41 00 02 A0 41 00 02 0C 42 00 02 0C 42 00 02 0C 42 BD E2 D4 99 11 35 49 9C 82 32 C2 D6 8E 00 01 8C AC B3 03 00 02 01 00 03 0F 61 77 73 2D 75 73 2D 77 65 73 74 2D 32 61 00 01 04 32 32 39 00 01 13 45 73 74 61 74 65 20 2F 20 48 6F 6D 65 73 74 65 61 64 00 01 01 26 82 90 5C 00 04 01 00 07')
print(RegionHandshake.from_bytes(data))
print()

# ImprovedInstantMessage
data = zerocode.hex2byte('C0 00 00 00 3C 00 FF FF 00 01 FE 77 9E 1D 56 55 00 01 4E 22 94 0A CD 7B 5A DD DB E0 00 11 28 C5 EF B6 FC AA 4E D5 9C F1 A6 40 D1 A9 92 72 01 00 03 BD E2 D4 99 11 35 49 9C 82 32 C2 D6 8E 00 01 8C AC 2A B0 E3 42 F3 15 A6 41 FD 8B BC 41 00 02 5F 5B F2 E0 A9 AA 00 01 F7 08 FB 6B 3B 8B 74 49 92 00 04 12 57 75 6C 66 69 65 20 52 65 61 6E 69 6D 61 74 6F 72 00 01 05 00 01 74 65 73 74 00 01 01 00 02 A5 A4 00 02')
print(ImprovedInstantMessage.from_bytes(data))
print()
data = zerocode.hex2byte('C0 00 00 0F BB 00 FF FF 00 01 FE 77 9E 1D 56 55 00 01 4E 22 94 0A CD 7B 5A DD DB E0 D6 D5 43 A0 A5 5E 43 6A A3 DE 58 3D 4C C5 25 25 00 01 8B 84 B5 DC B5 70 4A 77 93 05 3B A3 7A E0 C8 A9 00 20 01 00 01 FC 1A A8 8A E0 70 04 55 07 0F F6 D8 20 3D 13 49 00 04 12 57 75 6C 66 69 65 20 52 65 61 6E 69 6D 61 74 6F 72 00 01 0F 00 01 74 68 69 73 20 69 73 20 61 20 74 65 73 74 00 01 01 00 02')
# 77 9E 1D 56 55 00 01 4E 22 94 0A CD 7B 5A DD DB E0 D6 D5 43 A0 A5 5E 43 6A A3 DE 58 3D 4C C5 25 25 00 01 8B 84 B5 DC B5 70 4A 77 93 05 3B A3 7A E0 C8 A9 00 20 01 00 01 FC 1A A8 8A E0 70 04 55 07 0F F6 D8 20 3D 13 49 00 04 12 57 75 6C 66 69 65 20 52 65 61 6E 69 6D 61 74 6F 72 00 01 0F 00 01 74 68 69 73 20 69 73 20 61 20 74 65 73 74 00 01 01 00 02
print('UNENCODED', zerocode.byte2hex(zerocode.decode(data[6:])))
print(m := ImprovedInstantMessage.from_bytes(data))
print()
print(zerocode.byte2hex(m.to_bytes()))
