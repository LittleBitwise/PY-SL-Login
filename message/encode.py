from message.body import Message


def _to_bytes(self: Message):
    out = bytearray()

    # for i, (name, impl) in enumerate(self._keys.items()):
    for name, impl in self._keys.items():
        data = self.data(name)
        # print("CONVERTING", name, data.value, impl)

        if isinstance(data.value, (int, float)):
            out.extend(struct.pack(data.format, data.value))
        elif isinstance(data, (Variable1, Variable2)):
            _format = data.format[:2]
            out.extend(struct.pack(_format, data.length))
            _format = f"{data.length}s"
            out.extend(struct.pack(_format, data.value.encode()))
        elif isinstance(data, Uuid):
            out.extend(data.bytes)
        elif isinstance(data, Vector):
            out.extend(struct.pack(Vector.format, *data.value))
        elif isinstance(data, Rotation):
            out.extend(struct.pack(Rotation.format, *data.value))
        else:
            raise Exception("Unexpected data", data)
        # print('\t', type(value))
        # out.extend(value)

    if self._zerocoded:
        out = zerocode.encode(out)
    return bytes(out)


Message.to_bytes = _to_bytes
