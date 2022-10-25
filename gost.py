from functools import partial
from utils import xrange
from utils import strxor
from utils import hexdec
from utils import pad2
from utils import pad_size
from utils import unpad2


KEYSIZE = 8
BLOCKSIZE = 8
C1 = 0x01010104
C2 = 0x01010101

SEQ_ENCRYPT = (
    0, 1, 2, 3, 4, 5, 6, 7,
    0, 1, 2, 3, 4, 5, 6, 7,
    0, 1, 2, 3, 4, 5, 6, 7,
    7, 6, 5, 4, 3, 2, 1, 0,
)
SEQ_DECRYPT = (
    0, 1, 2, 3, 4, 5, 6, 7,
    7, 6, 5, 4, 3, 2, 1, 0,
    7, 6, 5, 4, 3, 2, 1, 0,
    7, 6, 5, 4, 3, 2, 1, 0,
)

SBOX = (
        (9, 6, 3, 2, 8, 11, 1, 7, 10, 4, 14, 15, 12, 0, 13, 5),
        (3, 7, 14, 9, 8, 10, 15, 0, 5, 2, 6, 12, 11, 4, 13, 1),
        (14, 4, 6, 2, 11, 3, 13, 8, 12, 15, 5, 10, 0, 7, 1, 9),
        (14, 7, 10, 12, 13, 1, 3, 9, 0, 2, 11, 4, 15, 8, 5, 6),
        (11, 5, 1, 9, 8, 13, 15, 0, 14, 4, 2, 3, 12, 7, 10, 6),
        (3, 10, 13, 12, 1, 2, 0, 11, 7, 5, 9, 4, 8, 15, 14, 6),
        (1, 13, 2, 9, 7, 10, 6, 0, 8, 12, 4, 5, 15, 3, 11, 14),
        (11, 10, 15, 5, 0, 12, 14, 8, 6, 2, 3, 9, 1, 7, 13, 4),
    )


def _K(s, _in):
    return (
        (s[0][(_in >> 0) & 0x0F] << 0) +
        (s[1][(_in >> 4) & 0x0F] << 4) +
        (s[2][(_in >> 8) & 0x0F] << 8) +
        (s[3][(_in >> 12) & 0x0F] << 12) +
        (s[4][(_in >> 16) & 0x0F] << 16) +
        (s[5][(_in >> 20) & 0x0F] << 20) +
        (s[6][(_in >> 24) & 0x0F] << 24) +
        (s[7][(_in >> 28) & 0x0F] << 28)
    )


def block2ns(data):
    data = bytearray(data)
    return (
        data[0] | data[1] << 8 | data[2] << 16 | data[3] << 24,
        data[4] | data[5] << 8 | data[6] << 16 | data[7] << 24,
    )


def ns2block(ns):
    n1, n2 = ns
    return bytes(bytearray((
        (n2 >> 0) & 0xFF, (n2 >> 8) & 0xFF, (n2 >> 16) & 0xFF, (n2 >> 24) & 0xFF,
        (n1 >> 0) & 0xFF, (n1 >> 8) & 0xFF, (n1 >> 16) & 0xFF, (n1 >> 24) & 0xFF,
    )))


def _shift11(x):
    return ((x << 11) & (2 ** 32 - 1)) | ((x >> (32 - 11)) & (2 ** 32 - 1))


def validate_key(key):
    if len(key) != KEYSIZE:
        raise ValueError("Неверный размер ключа")


def xcrypt(seq, sbox, key, ns):
    s = sbox
    w = bytearray(key)
    x = w[0] << 8
    n1, n2 = ns
    for i in seq:
        n1, n2 = _shift11(_K(s, (n1 + x) % (2 ** 32))) ^ n2, n1
    return n1, n2


def encrypt(sbox, key, ns):
    return xcrypt(SEQ_ENCRYPT, sbox, key, ns)


def decrypt(sbox, key, ns):
    return xcrypt(SEQ_DECRYPT, sbox, key, ns)


def ecb(key, data, action: bool, sbox=SBOX):
    # Режим ecb action == True шифрование, иначе расшифровка

    validate_key(key)
    result = []
    key = key.encode()
    for i in xrange(0, len(data), BLOCKSIZE):
        if action == True:
            key = int.from_bytes((ns2block(encrypt(
                sbox, key, block2ns(data[i:i + BLOCKSIZE])
            ))), 'big') ^ int.from_bytes(key, 'big')
            key = str(key).encode()
        else:
            result.append(ns2block(decrypt(
                sbox, key, block2ns(data[i:i + BLOCKSIZE])
            )))
    return int.from_bytes(key, 'big')


ecb_encrypt = partial(ecb, action=encrypt)
ecb_decrypt = partial(ecb, action=decrypt)


def cbc_encrypt(key, data, iv=8 * b"\x00", pad=True, sbox=SBOX, mesh=False):
    # Режим cbc шифровка

    validate_key(key)
    if pad:
        data = pad2(data, BLOCKSIZE)
    ciphertext = [iv]
    for i in xrange(0, len(data), BLOCKSIZE):
        if mesh and i >= MESH_MAX_DATA and i % MESH_MAX_DATA == 0:
            key, _ = meshing(key, iv, sbox=sbox)
        ciphertext.append(ns2block(encrypt(sbox, key, block2ns(
            strxor(ciphertext[-1], data[i:i + BLOCKSIZE])
        ))))
    return b"".join(ciphertext)


def cbc_decrypt(key, data, pad=True, sbox=SBOX, mesh=False):
    # Режим cbc расшифровка
    validate_key(key)
    iv = data[:BLOCKSIZE]
    plaintext = []
    for i in xrange(BLOCKSIZE, len(data), BLOCKSIZE):
        if (
                mesh and
                (i - BLOCKSIZE) >= MESH_MAX_DATA and
                (i - BLOCKSIZE) % MESH_MAX_DATA == 0
        ):
            key, _ = meshing(key, iv, sbox=sbox)
        plaintext.append(strxor(
            ns2block(decrypt(sbox, key, block2ns(data[i:i + BLOCKSIZE]))),
            data[i - BLOCKSIZE:i],
        ))
    if pad:
        plaintext[-1] = unpad2(plaintext[-1], BLOCKSIZE)
    return b"".join(plaintext)


def crt(key, data, iv=8 * b"\x00", sbox=SBOX):
    # Режим crt, для расшифровки используется эта же функция

    validate_key(key)
    n2, n1 = encrypt(sbox, key, block2ns(iv))
    gamma = []
    for _ in xrange(0, len(data) + pad_size(len(data), BLOCKSIZE), BLOCKSIZE):
        n1 = (n1 + C2) % (2 ** 32)
        n2 = (n2 + C1) % (2 ** 32 - 1)
        gamma.append(ns2block(encrypt(sbox, key, (n1, n2))))
    return strxor(b"".join(gamma), data)


MESH_CONST = hexdec("6900722264C904238D3ADB9646E92AC418FEAC9400ED0712C086DCC2EF4CA92B")
MESH_MAX_DATA = 1024


def meshing(key, iv, sbox=SBOX):

    key = ecb_decrypt(key, MESH_CONST, sbox=sbox)
    iv = ecb_encrypt(key, iv, sbox=sbox)
    return key, iv


def ofb_encrypt(key, data, iv=8 * b"\x00", sbox=SBOX, mesh=False):

    validate_key(key)
    ciphertext = [iv]
    for i in xrange(0, len(data) + pad_size(len(data), BLOCKSIZE), BLOCKSIZE):
        if mesh and i >= MESH_MAX_DATA and i % MESH_MAX_DATA == 0:
            key, iv = meshing(key, ciphertext[-1], sbox=sbox)
            ciphertext.append(strxor(
                data[i:i + BLOCKSIZE],
                ns2block(encrypt(sbox, key, block2ns(iv))),
            ))
            continue
        ciphertext.append(strxor(
            data[i:i + BLOCKSIZE],
            ns2block(encrypt(sbox, key, block2ns(ciphertext[-1]))),
        ))
    return b"".join(ciphertext[1:])


def ofb_decrypt(key, data, iv=8 * b"\x00", sbox=SBOX, mesh=False):

    validate_key(key)
    plaintext = []
    data = iv + data
    for i in xrange(BLOCKSIZE, len(data) + pad_size(len(data), BLOCKSIZE), BLOCKSIZE):
        if (
                mesh and
                (i - BLOCKSIZE) >= MESH_MAX_DATA and
                (i - BLOCKSIZE) % MESH_MAX_DATA == 0
        ):
            key, iv = meshing(key, data[i - BLOCKSIZE:i], sbox=sbox)
            plaintext.append(strxor(
                data[i:i + BLOCKSIZE],
                ns2block(encrypt(sbox, key, block2ns(iv))),
            ))
            continue
        plaintext.append(strxor(
            data[i:i + BLOCKSIZE],
            ns2block(encrypt(sbox, key, block2ns(data[i - BLOCKSIZE:i]))),
        ))
    return b"".join(plaintext)