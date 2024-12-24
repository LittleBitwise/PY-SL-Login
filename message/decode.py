from message.body import Message


@classmethod
def _from_bytes(cls: Message, data: bytes):
    """Parses packet bytes according to message fields."""

    def unpack_sequence(buffer: bytes, *args):
        """Unpacks bytes from buffer according to struct format strings"""
        out = []
        offset = 0
        last_val = None
        for format in map(str, args):
            # print(f'FORMAT {format:<4}', 'AHEAD', zerocode.byte2hex(buffer[offset:offset+4]), 'OFFSET', offset) # NOQA
            if format == Variable1.format:
                [length] = struct.unpack_from(U8.format, buffer, offset)
                # print('VAR1 LENGTH', str(length))
                [string] = struct.unpack_from(f"{str(length)}s", buffer, offset + 1)
                out.append((length, string))
                last_val = None
                offset += 1 + length
                continue
            if format == Variable2.format:
                [length] = struct.unpack_from(U16.format, buffer, offset)
                # print('VAR2 LENGTH', str(length))
                [string] = struct.unpack_from(f"{str(length)}s", buffer, offset + 2)
                out.append((length, string))
                last_val = None
                offset += 2 + length
                continue
            if "*" in format and last_val is not None:
                format = format.replace("*", str(last_val))
            if format == "0s":
                out.append(b"")
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
    formats = []
    for x in message._keys.values():
        if not isinstance(x, tuple):
            formats.append(x.format)
        else:
            repeat: Variable1 = x[0]
            raise Exception("TODO: solve for variable length blocks")
            block: dict = x[1]
            for _ in range(repeat):
                for y in block.values():
                    formats.append(y.format)
    # print('FORMATS', formats)
    if message._zerocoded:
        data = data[body_byte:]
        data = zerocode.decode(data)
        # print(zerocode.byte2hex(data))
        data = data[message._frequency :]
        unpacked = unpack_sequence(data, *formats)
    else:
        data = data[body_byte + message._frequency :]
        # print(zerocode.byte2hex(data))
        unpacked = unpack_sequence(data, *formats)

    # print('UNPACKED', unpacked)
    for i, (name, impl) in enumerate(message._keys.items()):  # assign
        # print('ASSIGN', name, unpacked[i], impl, '->', impl(unpacked[i]))
        message[name] = impl(unpacked[i])
    return message


Message.from_bytes = _from_bytes
