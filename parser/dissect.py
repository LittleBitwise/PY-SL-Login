import parser.template
import parser.zerocode

import packet


def parse():
    """
    Reads plain-text exported packet dissections from Wireshark.

    Expects packet format to be only bytes, no summary or details.
    """
    UDP_HEADER = 126
    BYTE_COL = 6
    BYTE_DATA = 54

    with open("dissect.txt", "r") as file:

        def console_print(data: bytes):
            print()
            data = data.rstrip()[UDP_HEADER:]
            data_bytes = parser.zerocode.hex2byte(data)
            message_num = packet.message_number(data_bytes)
            message_name = parser.template.message[message_num]
            print(packet.human_header(data_bytes), message_name)
            print(data)
            print()

        data = ""
        for line in map(str.strip, file):
            if not line:
                console_print(data)
                data = ""
                continue
            data += line[BYTE_COL:BYTE_DATA]


if __name__ == "__main__":
    parse()
