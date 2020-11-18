import base64
try:
    from coincurve import PrivateKey, PublicKey
except ImportError:
    print("Can't import coincurve, can't verify and sign tx.")
from .define import Define
from .coder import VarInt, Coder
from .address import Address
from .base_data import BaseNulsData

class NulsSignature(BaseNulsData):
    ALG_TYPE = 0 # only one for now...

    def __init__(self, data=None):
        self.pub_key = None
        self.digest_bytes = None
        self.sig_ser = None
        if data is not None:
            self.parse(data)

    def parse(self, buffer, cursor=0):
        pos, self.pub_key = Coder.readByLength(buffer, cursor)
        cursor += pos
        self.ecc_type = buffer[cursor]
        cursor += 1
        pos, self.sig_ser = Coder.readByLength(buffer, cursor)
        cursor += pos
        return cursor

    @staticmethod
    def signData(pri_key, digest_bytes):
        privkey = PrivateKey(pri_key) # we expect to have a private key as bytes. unhexlify it before passing.
        item = NulsSignature()
        item.pub_key = privkey.public_key.format()
        item.digest_bytes = digest_bytes
        item.sig_ser = privkey.sign(digest_bytes, hasher=None)
        return item

    @staticmethod
    def signMessage(pri_key, message):
       return NulsSignature.signRecoverableMessage(pri_key, message)

    def serialize(self, with_length=False):
        output = b''
        output += Coder.writeWithLength(self.pub_key)
        output += Coder.writeWithLength(self.sig_ser)
        if with_length:
            return Coder.writeWithLength(output)
        else:
            return output

    def verify(self, message):
        pub = PublicKey(self.pub_key)
        message = VarInt(len(message)).encode() + message
        try:
            # sig_raw = pub.ecdsa_deserialize(self.sig_ser)
            good = pub.verify(self.sig_ser, Define.MESSAGE_TEMPLATE % message)
        except Exception:
            print("Verification failed")
            good = False
        return good
    
    @staticmethod
    def coincurveSig(electrum_signature):
        if len(electrum_signature) != Define.LEN_COMPACT_SIG:
            raise ValueError('Not a 65-byte compact signature.')
        # Compute coincurve recid
        recid = electrum_signature[0] - Define.RECID_UNCOMPR
        if not (Define.RECID_MIN <= recid <= Define.RECID_MAX):
            raise ValueError('Recovery ID %d is not supported.' % recid)
        recid_byte = int.to_bytes(recid, length=1, byteorder='big')
        return electrum_signature[1:] + recid_byte
    
    @staticmethod
    def electrumSig(coincurve_signature):
        if len(coincurve_signature) != Define.LEN_COMPACT_SIG:
            raise ValueError('Not a 65-byte compact signature.')
        # Compute Electrum recid
        recid = coincurve_signature[-1] + Define.RECID_UNCOMPR
        if not (Define.RECID_UNCOMPR + Define.RECID_MIN <= recid <= Define.RECID_UNCOMPR + Define.RECID_MAX):
            raise ValueError('Recovery ID %d is not supported.' % recid)
        recid_byte = int.to_bytes(recid, length=1, byteorder='big')
        return recid_byte + coincurve_signature[0:-1]
    
    @staticmethod
    def prepareMessage(msg):
        msg = VarInt(len(msg)).encode() + msg
        msg = Define.MESSAGE_TEMPLATE % msg
        return msg
    
    @staticmethod
    def signRecoverableMessage(pri_key, message):
        message = prepareMessage(message)
        privkey = PrivateKey(pri_key) # we expect to have a private key as bytes. unhexlify it before passing.
        sig_check = privkey.sign_recoverable(message)
        return electrumSig(sig_check)
    
    @staticmethod
    def recoverMessageAddress(signature, message, chain_id=1, prefix=None, address_type=1):
        """ Verifies a signature of a hash and returns the address that signed it.
        If no address is returned, signature is bad.
        """
        message = prepareMessage(message)
        pub = PublicKey.from_signature_and_message(coincurveSig(signature), message)
        addr_hash = Address.publicKeyToHash(pub.format(), chain_id=chain_id, address_type=address_type)
        if prefix is None:
            prefix = Define.NETWORKS[chain_id]
        address = Address.addressFromHash(addr_hash, prefix=prefix)
        return address
