from .coder import Coder, VarInt
from .base_data import BaseNulsData

class Coin(BaseNulsData):
    def __init__(self, data=None):
        self.address = None
        self.rawScript = None
        self.fromHash = None
        self.fromIndex = None
        self.na = None
        self.lockTime = None
        if data is not None:
            self.parse(data)

    def parse(self, buffer, cursor=0):
        pos, owner = Coder.readByLength(buffer, cursor)
        cursor += pos
        if len(owner) == (Define.HASH_LENGTH + 1):
            val = (len(owner) - Define.HASH_LENGTH)
            if (val > 1):
                fc = VarInt()
                fc.parse(owner, Define.HASH_LENGTH)
                self.fromIndex = fc.value
                assert fc.originallyEncodedSize == val
            else:
                self.fromIndex = owner[-1]
            self.fromHash = owner[:Define.HASH_LENGTH]
        elif len(owner) == Define.ADDRESS_LENGTH:
            self.address = owner
        else:
            # ok, we have some script here
            self.rawScript = owner
            # tentative fix for now... Ugly.
            self.address = owner[2:Define.ADDRESS_LENGTH + 2]  # it's either 2 or 3.
            # print(address_from_hash(owner[3:ADDRESS_LENGTH+3]))

        self.na = struct.unpack("Q", buffer[cursor:cursor + 8])[0]
        cursor += 8
        self.lockTime = Coder.readUint48(buffer, cursor)
        cursor += 6
        return cursor

    def toDict(self):
        val = {'value': self.na, 'lockTime': self.lockTime}
        if self.rawScript is not None:
            val['owner'] = self.rawScript.hex()

        if self.address is not None:
            val['address'] = Address.addressFromHash(self.address)
            val['addressHash'] = self.address

        if self.fromHash is not None:
            val['fromHash'] = self.fromHash.hex()
            val['fromIndex'] = self.fromIndex

        return val

    @staticmethod
    def fromDict(value):
        item = Coin()
        item.address = value.get('address', None)
        item.assetsChainId = value.get('assetsChainId', None)
        item.assetsId = value.get('assetsId', None)

        item.fromIndex = value.get('fromIndex', None)
        item.lockTime = value.get('lockTime', 0)
        item.na = value.get('value', None)

        return item

    def __repr__(self):
        return "<UTXO Coin: {}: {} - {}>".format((self.address or self.fromHash).hex(), self.na, self.lockTime)

    def serialize(self):
        output = b""
        if self.rawScript is not None:
            output += Coder.writeWithLength(self.rawScript)
        elif self.fromHash is not None:
            output += Coder.writeWithLength(self.fromHash + bytes([self.fromIndex]))
        elif self.address is not None:
            output += Coder.writeWithLength(self.address)
        else:
            raise ValueError("Either fromHash and fromId should be set or address.")

        output += struct.pack("Q", self.na)
        output += Coder.writeUint48(self.lockTime)
        return output

class CoinData(BaseNulsData):
    def __init__(self, data=None):
        self.from_count = None
        self.to_count = None
        self.inputs = list()
        self.outputs = list()

    async def parse(self, buffer, cursor=0):
        if buffer[cursor:cursor + 4] == Define.PLACE_HOLDER:
            return cursor + 4

        fc = VarInt()
        fc.parse(buffer, cursor)
        self.from_count = fc.value
        cursor += fc.originallyEncodedSize
        self.inputs = list()
        for i in range(self.from_count):
            coin = Coin()
            cursor = coin.parse(buffer, cursor)
            self.inputs.append(coin)

        tc = VarInt()
        tc.parse(buffer, cursor)
        self.to_count = tc.value
        cursor += tc.originallyEncodedSize
        #self.to_count = buffer[cursor]
        self.outputs = list()
        for i in range(self.to_count):
            coin = Coin()
            cursor = coin.parse(buffer, cursor)
            self.outputs.append(coin)

        return cursor

    def getFee(self):
        return (sum([i.na for i in self.inputs]) - sum([o.na for o in self.outputs]))

    def getOutputSum(self):
        return sum([o.na for o in self.outputs])

    async def serialize(self):
        output = b""
        output += VarInt(len(self.inputs)).encode()
        for coin in self.inputs:
            output += coin.serialize()
        output += VarInt(len(self.outputs)).encode()
        for coin in self.outputs:
            output += coin.serialize()

        return output

class NulsDigestData(BaseNulsData):
    HASH_LENGTH = 34
    DIGEST_ALG_SHA256 = 0
    DIGEST_ALG_SHA160 = 1

    def __init__(self, data=None, alg_type=None):
        self.digest_bytes = None
        self.alg_type = None

        if data is not None and alg_type is None:
            self.parse(data)

        elif data is not None and alg_type is not None:
            self.digest_bytes = data
            self.alg_type = alg_type

    @property
    def size(self):
        return self.HASH_LENGTH

    def parse(self, buffer, cursor=0):
        self.alg_type = buffer[cursor]
        pos, self.digest_bytes = Coder.readByLength(buffer, cursor=cursor + 1)

    def serialize(self):
        return bytes([self.alg_type, len(self.digest_bytes)]) + self.digest_bytes

    def __str__(self):
        return self.serialize().hex()