
from binascii import hexlify, unhexlify


B58_DIGITS = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


class Base58(object):

    @staticmethod
    def encode(b):
        """Encode bytes to a base58-encoded string"""

        # Convert big-endian bytes to integer
        n = int('0x0' + hexlify(b).decode('utf8'), 16)

        # Divide that integer into bas58
        res = []
        while n > 0:
            n, r = divmod(n, 58)
            res.append(B58_DIGITS[r])
        res = ''.join(res[::-1])

        # Encode leading zeros as base58 zeros
        czero = 0
        pad = 0
        for c in b:
            if c == czero:
                pad += 1
            else:
                break
        return B58_DIGITS[0] * pad + res

    @staticmethod
    def decode(s):
        """Decode a base58-encoding string, returning bytes"""
        if not s:
            return b''

        # Convert the string to an integer
        n = 0
        for c in s:
            n *= 58
            if c not in B58_DIGITS:
                raise ValueError('Character %r is not a valid base58 character' % c)
            digit = B58_DIGITS.index(c)
            n += digit

        # Convert the integer to bytes
        h = '%x' % n
        if len(h) % 2:
            h = '0' + h
        res = unhexlify(h.encode('utf8'))

        # Add padding back.
        pad = 0
        for c in s[:-1]:
            if c == B58_DIGITS[0]:
                pad += 1
            else:
                break

        return b'\x00' * pad + res

    @staticmethod
    def getXoR(body):
        xor = 0
        for c in body:
            xor ^= c
        return xor
