from io import BytesIO
import struct
from typing import BinaryIO
import uuid

demo_data = bytearray.fromhex('FE FF 04 00 12 00 00 00 0B 00 00 00 41 00 63 00 74 00 69 00 76 00 69 00 74 00 79 00 49 00 64 00 00 00 80 4A FE 14 98 16 9F 40 8A 13 31 70 63 B2 4A A4 07 00 12 00 00 00 11 00 00 00 41 00 64 00 64 00 69 00 74 00 69 00 6F 00 6E 00 61 00 6C 00 50 00 61 00 72 00 61 00 6D 00 73 00 00 00 FE FF 04 00 12 00 00 00 09 00 00 00 53 00 77 00 69 00 74 00 63 00 68 00 49 00 64 00 00 00 B8 B7 8C C0 3C 9B 8E 40 8E 30 5E 16 A3 AE B4 44 04 00 12 00 00 00 0D 00 00 00 53 00 77 00 69 00 74 00 63 00 68 00 50 00 6F 00 72 00 74 00 49 00 64 00 00 00 CC C4 E8 89 02 42 82 45 95 4B 7D 9E AF 39 FB 91 05 00 12 00 00 00 10 00 00 00 56 00 6D 00 53 00 77 00 69 00 74 00 63 00 68 00 4E 00 69 00 63 00 4E 00 61 00 6D 00 65 00 00 00 4B 00 00 00 34 00 33 00 30 00 30 00 38 00 39 00 34 00 33 00 2D 00 39 00 41 00 38 00 44 00 2D 00 35 00 41 00 42 00 32 00 2D 00 38 00 37 00 46 00 39 00 2D 00 33 00 44 00 31 00 35 00 30 00 37 00 32 00 34 00 41 00 46 00 31 00 31 00 2D 00 2D 00 46 00 43 00 37 00 38 00 35 00 32 00 32 00 35 00 2D 00 39 00 31 00 33 00 31 00 2D 00 35 00 36 00 36 00 31 00 2D 00 41 00 43 00 30 00 43 00 2D 00 33 00 41 00 31 00 35 00 37 00 43 00 36 00 31 00 41 00 45 00 31 00 35 00 00 00 FD FF 03 00 12 00 00 00 1A 00 00 00 43 00 72 00 65 00 61 00 74 00 65 00 50 00 72 00 6F 00 63 00 65 00 73 00 73 00 69 00 6E 00 67 00 53 00 74 00 61 00 72 00 74 00 54 00 69 00 6D 00 65 00 00 00 DB D0 BF 89 F7 92 D8 01 05 00 12 00 00 00 0E 00 00 00 44 00 4E 00 53 00 53 00 65 00 72 00 76 00 65 00 72 00 4C 00 69 00 73 00 74 00 00 00 0B 00 00 00 31 00 37 00 32 00 2E 00 31 00 38 00 2E 00 31 00 2E 00 31 00 00 00 05 00 12 00 00 00 0A 00 00 00 44 00 4E 00 53 00 53 00 75 00 66 00 66 00 69 00 78 00 00 00 14 00 00 00 7A 00 71 00 32 00 2E 00 6C 00 6F 00 63 00 61 00 6C 00 2E 00 63 00 69 00 72 00 6E 00 6F 00 2E 00 78 00 79 00 7A 00 00 00 01 00 12 00 00 00 19 00 00 00 45 00 6E 00 61 00 62 00 6C 00 65 00 4C 00 6F 00 77 00 49 00 6E 00 74 00 65 00 72 00 66 00 61 00 63 00 65 00 4D 00 65 00 74 00 72 00 69 00 63 00 00 00 01 00 00 00 02 00 12 00 00 00 0E 00 00 00 45 00 6E 00 63 00 61 00 70 00 4F 00 76 00 65 00 72 00 68 00 65 00 61 00 64 00 00 00 00 00 00 00 02 00 12 00 00 00 06 00 00 00 46 00 6C 00 61 00 67 00 73 00 00 00 00 00 00 00 05 00 12 00 00 00 0F 00 00 00 47 00 61 00 74 00 65 00 77 00 61 00 79 00 41 00 64 00 64 00 72 00 65 00 73 00 73 00 00 00 0D 00 00 00 31 00 37 00 32 00 2E 00 32 00 37 00 2E 00 31 00 37 00 36 00 2E 00 31 00 00 00 04 00 12 00 00 00 0E 00 00 00 47 00 6E 00 73 00 49 00 6E 00 73 00 74 00 61 00 6E 00 63 00 65 00 49 00 64 00 00 00 43 89 00 43 8D 9A B2 5A 87 F9 3D 15 07 24 AF 11 04 00 32 00 00 00 03 00 00 00 49 00 44 00 00 00 CC C4 E8 89 02 42 82 45 95 4B 7D 9E AF 39 FB 91 08 00 12 00 00 00 11 00 00 00 49 00 70 00 43 00 6F 00 6E 00 66 00 69 00 67 00 75 00 72 00 61 00 74 00 69 00 6F 00 6E 00 73 00 00 00 01 00 00 00 FE FF 05 00 12 00 00 00 0A 00 00 00 49 00 70 00 41 00 64 00 64 00 72 00 65 00 73 00 73 00 00 00 0E 00 00 00 31 00 37 00 32 00 2E 00 32 00 37 00 2E 00 31 00 38 00 31 00 2E 00 33 00 33 00 00 00 04 00 12 00 00 00 0B 00 00 00 49 00 70 00 53 00 75 00 62 00 6E 00 65 00 74 00 49 00 64 00 00 00 9B E6 AC DB 0D 66 A4 45 BD 91 1C CE 94 20 11 46 02 00 12 00 00 00 0D 00 00 00 50 00 72 00 65 00 66 00 69 00 78 00 4C 00 65 00 6E 00 67 00 74 00 68 00 00 00 14 00 00 00 FD FF 05 00 12 00 00 00 0B 00 00 00 4D 00 61 00 63 00 41 00 64 00 64 00 72 00 65 00 73 00 73 00 00 00 12 00 00 00 30 00 30 00 2D 00 31 00 35 00 2D 00 35 00 44 00 2D 00 39 00 35 00 2D 00 46 00 32 00 2D 00 45 00 35 00 00 00 05 00 12 00 00 00 05 00 00 00 4E 00 61 00 6D 00 65 00 00 00 09 00 00 00 45 00 74 00 68 00 65 00 72 00 6E 00 65 00 74 00 00 00 02 00 22 00 00 00 0B 00 00 00 4F 00 62 00 6A 00 65 00 63 00 74 00 54 00 79 00 70 00 65 00 00 00 03 00 00 00 08 00 12 00 00 00 09 00 00 00 50 00 6F 00 6C 00 69 00 63 00 69 00 65 00 73 00 00 00 01 00 00 00 FE FF 02 00 12 00 00 00 0D 00 00 00 45 00 78 00 74 00 65 00 72 00 6E 00 61 00 6C 00 50 00 6F 00 72 00 74 00 00 00 91 CC 00 00 02 00 12 00 00 00 0D 00 00 00 49 00 6E 00 74 00 65 00 72 00 6E 00 61 00 6C 00 50 00 6F 00 72 00 74 00 00 00 B3 15 00 00 05 00 12 00 00 00 09 00 00 00 50 00 72 00 6F 00 74 00 6F 00 63 00 6F 00 6C 00 00 00 04 00 00 00 54 00 43 00 50 00 00 00 05 00 12 00 00 00 05 00 00 00 54 00 79 00 70 00 65 00 00 00 04 00 00 00 4E 00 41 00 54 00 00 00 FD FF 06 00 12 00 00 00 11 00 00 00 53 00 68 00 61 00 72 00 65 00 64 00 43 00 6F 00 6E 00 74 00 61 00 69 00 6E 00 65 00 72 00 73 00 00 00 00 00 00 00 03 00 12 00 00 00 0A 00 00 00 53 00 74 00 61 00 72 00 74 00 54 00 69 00 6D 00 65 00 00 00 02 C1 C0 89 F7 92 D8 01 02 00 12 00 00 00 06 00 00 00 53 00 74 00 61 00 74 00 65 00 00 00 02 00 00 00 05 00 11 00 00 00 05 00 00 00 54 00 79 00 70 00 65 00 00 00 04 00 00 00 4E 00 41 00 54 00 00 00 03 00 12 00 00 00 08 00 00 00 56 00 65 00 72 00 73 00 69 00 6F 00 6E 00 00 00 00 00 00 00 0F 00 00 00 04 00 12 00 00 00 0F 00 00 00 56 00 69 00 72 00 74 00 75 00 61 00 6C 00 4D 00 61 00 63 00 68 00 69 00 6E 00 65 00 00 00 43 89 00 43 8D 9A B2 5A 87 F9 3D 15 07 24 AF 11 05 00 12 00 00 00 0F 00 00 00 56 00 69 00 72 00 74 00 75 00 61 00 6C 00 4E 00 65 00 74 00 77 00 6F 00 72 00 6B 00 00 00 25 00 00 00 61 00 37 00 39 00 66 00 37 00 38 00 65 00 32 00 2D 00 61 00 33 00 38 00 63 00 2D 00 34 00 66 00 37 00 31 00 2D 00 62 00 63 00 38 00 63 00 2D 00 62 00 39 00 33 00 65 00 31 00 33 00 34 00 66 00 39 00 66 00 32 00 34 00 00 00 05 00 12 00 00 00 13 00 00 00 56 00 69 00 72 00 74 00 75 00 61 00 6C 00 4E 00 65 00 74 00 77 00 6F 00 72 00 6B 00 4E 00 61 00 6D 00 65 00 00 00 0E 00 00 00 42 00 6C 00 75 00 65 00 73 00 74 00 61 00 63 00 6B 00 73 00 4E 00 78 00 74 00 00 00 FD FF')

def _bytes_to_int(b):
    return int.from_bytes(b, 'little')

def read_string(io: BinaryIO):
    size = _bytes_to_int(io.read(4)) * 2
    return io.read(size).decode('utf-16-le')[:-1]

def read_kvpair(io: BinaryIO):
    typeid = struct.unpack('<H', io.read(2))[0]
    if typeid == 0xFFFD:
        raise StopIteration
    flags = struct.unpack('<I', io.read(4))[0]
    name = read_string(io)
    value_len = -1
    if typeid == 0x04:
        # GUID
        value_len = 16
        value_factory = lambda b: str(uuid.UUID(bytes_le=b))
    elif typeid == 0x02:
        # int32
        value_len = 4
        value_factory = _bytes_to_int
    elif typeid == 0x03:
        # int64
        value_len = 8
        value_factory = _bytes_to_int
    elif typeid == 0x01:
        # bool
        value_len = 4
        value_factory = lambda b: bool(_bytes_to_int(b))

    if value_len != -1:
        value = value_factory(io.read(value_len))
        return name, value

    if typeid == 0x05:
        # string
        return name, read_string(io)
    elif typeid == 0x06:
        # array of string
        array_len = _bytes_to_int(io.read(4))
        return name, [read_string(io) for _ in range(array_len)]
    elif typeid == 0x07:
        # mapping
        return name, read_mapping(io)
    elif typeid == 0x08:
        # array of mapping
        array_len = _bytes_to_int(io.read(4))
        return name, [read_mapping(io) for _ in range(array_len)]

    raise ValueError(f'unknown typeid {typeid}')

def read_mapping(io: BinaryIO):
    magic = struct.unpack('<H', io.read(2))[0]
    assert magic == 0xFFFE
    result = {}
    while True:
        try:
            name, value = read_kvpair(io)
            result[name] = value
        except StopIteration:
            # the end flag is consumed by the read_kvpair function
            break
    return result

def dump_endpoints_state() -> dict[str, dict]:
    import winreg
    result = {}
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services\HNS\State\HostComputeNetwork\VolatileStore\Endpoint') as hkey:
        i = 0
        while True:
            try:
                name, value, valtype = winreg.EnumValue(hkey, i)
                i += 1
                if valtype != winreg.REG_BINARY:
                    continue
                result[name] = read_mapping(BytesIO(value))
            except OSError:
                break
    return result

def _test():
    import pprint
    pprint.pprint(dump_endpoints_state())

if __name__ == '__main__':
    _test()
