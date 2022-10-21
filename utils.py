from codecs import getdecoder
from codecs import getencoder
from sys import version_info


xrange = range if version_info[0] == 3 else xrange


def strxor(a, b):
    mlen = min(len(a), len(b))
    a, b, xor = bytearray(a), bytearray(b), bytearray(mlen)
    for i in xrange(mlen):
        xor[i] = a[i] ^ b[i]
    return bytes(xor)


_hexdecoder = getdecoder("hex")
_hexencoder = getencoder("hex")


def hexdec(data):
    return _hexdecoder(data)[0]


def pad_size(data_size, blocksize):
    if data_size < blocksize:
        return blocksize - data_size
    if data_size % blocksize == 0:
        return 0
    return blocksize - data_size % blocksize


def pad2(data, blocksize):
    return data + b"\x80" + b"\x00" * pad_size(len(data) + 1, blocksize)


def unpad2(data, blocksize):
    last_block = bytearray(data[-blocksize:])
    pad_index = last_block.rfind(b"\x80")
    if pad_index == -1:
        raise ValueError("Ошибка данных")
    for c in last_block[pad_index + 1:]:
        if c != 0:
            raise ValueError("Ошибка данных")
    return data[:-(blocksize - pad_index)]