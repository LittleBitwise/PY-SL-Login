from parser import zerocode

from message import body
from message.body import Message
from packet.types import Fixed, Frequency, High, Low, Medium  # NOQA


def body_decode_encode(cls_body: Message, offset: int, hexa: str):
    data = zerocode.hex2byte(hexa)
    m = cls_body.from_bytes(data)
    data = zerocode.byte2hex(m.to_bytes())

    assert data == hexa[18 + 3 * offset :]


def test_1():
    body_decode_encode(
        body.StartPingCheck,
        High.size,
        "00 00 00 00 38 00 01 01 37 00 00 00",
    )


def test_2():
    # NOTE: TO_BYTES CONVERSION MISSING LAST 78 BYTES
    body_decode_encode(
        body.RegionHandshake,
        Low.size + 1,
        "C0 00 00 00 02 00 FF FF 00 01 94 26 82 90 5C 15 08 46 69 64 65 6C 69 73 00 01 02 64 28 B1 50 71 47 2F 9C DB E2 85 CC 39 DA 9E 00 01 CD CC A0 41 00 04 FB FE A8 13 09 AD 3D 92 3A DD 36 DC 7E BB 13 47 9C 43 4A 43 D5 D8 A3 DD B6 24 41 67 82 38 34 78 AB B7 83 E6 3E 93 26 C0 24 8A 24 76 66 85 5D A3 17 9C DA BD 39 8A 9B 6B 13 91 4D C3 33 BA 32 1F BE B1 69 C7 11 EA FF F2 EF E5 0F 24 DC 88 1D F2 CB 1C BC 94 17 46 88 17 AA 35 9E 0A 50 4C 89 FA F3 1A AE 95 84 09 97 94 F7 C8 59 35 13 62 6C 77 DB A2 21 E5 81 35 19 E9 94 7C 03 4F 3E DF A1 C9 DB A2 21 E5 81 35 19 E9 94 7C 03 4F 3E DF A1 C9 00 02 30 41 00 02 A0 41 00 02 A0 41 00 02 A0 41 00 02 A0 41 00 02 0C 42 00 02 0C 42 00 02 0C 42 BD E2 D4 99 11 35 49 9C 82 32 C2 D6 8E 00 01 8C AC B3 03 00 02 01 00 03 0F 61 77 73 2D 75 73 2D 77 65 73 74 2D 32 61 00 01 04 32 32 39 00 01 13 45 73 74 61 74 65 20 2F 20 48 6F 6D 65 73 74 65 61 64 00 01 01 26 82 90 5C 00 04 01 00 07",  # NOQA
    )


def test_3():
    # NOTE: TO_BYTES CONVERSION MISSING LAST 4 BYTES (A5 A4 00 02)
    body_decode_encode(
        body.ImprovedInstantMessage,
        Low.size + 1,
        "C0 00 00 00 3C 00 FF FF 00 01 FE 77 9E 1D 56 55 00 01 4E 22 94 0A CD 7B 5A DD DB E0 00 11 28 C5 EF B6 FC AA 4E D5 9C F1 A6 40 D1 A9 92 72 01 00 03 BD E2 D4 99 11 35 49 9C 82 32 C2 D6 8E 00 01 8C AC 2A B0 E3 42 F3 15 A6 41 FD 8B BC 41 00 02 5F 5B F2 E0 A9 AA 00 01 F7 08 FB 6B 3B 8B 74 49 92 00 04 12 57 75 6C 66 69 65 20 52 65 61 6E 69 6D 61 74 6F 72 00 01 05 00 01 74 65 73 74 00 01 01 00 02 A5 A4 00 02",  # NOQA
    )


def test_4():
    body_decode_encode(
        body.ImprovedInstantMessage,
        Low.size + 1,
        "C0 00 00 0F BB 00 FF FF 00 01 FE 77 9E 1D 56 55 00 01 4E 22 94 0A CD 7B 5A DD DB E0 D6 D5 43 A0 A5 5E 43 6A A3 DE 58 3D 4C C5 25 25 00 01 8B 84 B5 DC B5 70 4A 77 93 05 3B A3 7A E0 C8 A9 00 20 01 00 01 FC 1A A8 8A E0 70 04 55 07 0F F6 D8 20 3D 13 49 00 04 12 57 75 6C 66 69 65 20 52 65 61 6E 69 6D 61 74 6F 72 00 01 0F 00 01 74 68 69 73 20 69 73 20 61 20 74 65 73 74 00 01 01 00 02",  # NOQA
    )
