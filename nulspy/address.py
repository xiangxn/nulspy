from .base58 import Base58
from .define import Define
import string
import hashlib
import struct


class Address(object):
    @staticmethod
    def addressFromHash(addr, prefix=None, chain_id=1):
        if not prefix:
            prefix = Define.NETWORKS[chain_id]
        addr = Base58.encode(addr + bytes((Base58.getXoR(addr), )))
        return prefix + string.ascii_letters[len(prefix) - 1] + addr

    @staticmethod
    def hashFromAddress(address):
        if address.startswith(Define.NETWORKS[1]):
            address = address[5:]
        elif address.startswith(Define.NETWORKS[2]):
            address = address[6:]
        else:
            raise NotImplementedError("transfers on other chains not implemented yet!")
        return Base58.decode(address)[:-1]

    @staticmethod
    def publicKeyToHash(pub_key, chain_id=1, address_type=1):
        sha256_digest = hashlib.sha256(pub_key).digest()
        md160_digest = hashlib.new('ripemd160', sha256_digest).digest()
        computed_address = bytes(struct.pack("h", chain_id)) + bytes([address_type]) + md160_digest
        return computed_address

    @staticmethod
    def getAddress(pubkey, chain_id=1, prefix=None):
        phash = Address.publicKeyToHash(pubkey, chain_id=chain_id)
        if prefix is None:
            prefix = Define.NETWORKS[chain_id]
        address = Address.addressFromHash(phash, prefix=prefix)
        return address