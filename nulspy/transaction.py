import struct
import math
from .define import Define
from .coder import Coder, VarInt
from .address import Address
from .base_data import BaseNulsData
from .signature import NulsSignature, NulsDigestData
from .trxs.register import TX_TYPES_REGISTER

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
        if len(owner) == (Define.HASH_LENGTH+1):
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
            self.address = owner[2:Define.ADDRESS_LENGTH+2] # it's either 2 or 3.
            # print(address_from_hash(owner[3:ADDRESS_LENGTH+3]))

        self.na = struct.unpack("Q", buffer[cursor:cursor+8])[0]
        cursor += 8
        self.lockTime = Coder.readUint48(buffer, cursor)
        cursor += 6
        return cursor

    def toDict(self):
        val = {
            'value': self.na,
            'lockTime': self.lockTime
        }
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
        if buffer[cursor:cursor+4] == Define.PLACE_HOLDER:
            return cursor+4

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

class Transaction(BaseNulsData):
    def __init__(self):
        self.type = None
        self.time = None
        self.remark = None
        self.txData = None
        self.raw_coin_data = b''
        self.raw_tx_data = b''
        self.raw_signature = b''
        self.hash = None
        self.signature = None
        # self.scriptSig = None
        self.module_data = dict()
        # self.coin_data = CoinData()
        self.inputs = []
        self.outputs = []

    async def _parse_data(self, buffer, cursor=0):
        if self.type in TX_TYPES_REGISTER:
            cursor, self.module_data = await TX_TYPES_REGISTER[self.type].fromBuffer(buffer, cursor)
        else:
            cursor += len(Define.PLACE_HOLDER)
        return cursor

    async def _write_data(self):
        output = b""
        if self.type in TX_TYPES_REGISTER:
            output += await TX_TYPES_REGISTER[self.type].toBuffer(self.module_data)
        return output
    
    async def _write_coin_data(self):
        output = b""
        output += VarInt(len(self.inputs)).encode()
        for coin in self.inputs:
            output += Coder.writeWithLength(Address.hashFromAddress(coin.get('address')))
            output += struct.pack("H", coin.get('assetsChainId'))
            output += struct.pack("H", coin.get('assetsId'))
            output += coin.get('amount').to_bytes(32, 'little')
            # output += struct.pack("Q", coin.get('amount'))
            output += Coder.writeWithLength(bytes.fromhex(coin.get('nonce')))
            output += bytes([coin.get('locked')])
            
        output += VarInt(len(self.outputs)).encode()
        for coin in self.outputs:
            output += Coder.writeWithLength(Address.hashFromAddress(coin.get('address')))
            output += struct.pack("H", coin.get('assetsChainId'))
            output += struct.pack("H", coin.get('assetsId'))
            # output += struct.pack("Q", coin.get('amount'))
            output += coin.get('amount').to_bytes(32, 'little')
            if coin.get('lockTime') == -1:
                output += bytes.fromhex("ffffffffffffffffff")
            else:
                output += struct.pack("Q", coin.get('lockTime'))
        return output
        
    async def _read_coin_data(self, buffer, cursor=0):
        if not len(buffer):
            return

        fc = VarInt()
        fc.parse(buffer, cursor)
        self.from_count = fc.value
        cursor += fc.originallyEncodedSize
        self.inputs = list()
        for i in range(self.from_count):
            coin = dict()
            pos, owner = Coder.readByLength(buffer, cursor)
            cursor += pos
            coin['address'] = owner
            coin['assetsChainId'] = struct.unpack("H", buffer[cursor:cursor+2])[0]
            cursor += 2
            coin['assetsId'] = struct.unpack("H", buffer[cursor:cursor+2])[0]
            cursor += 2
            coin['amount'] = struct.unpack("Q", buffer[cursor:cursor+2])[0]
            cursor += 8
            pos, nonce = Coder.readByLength(buffer, cursor)
            cursor += pos
            coin['address'] = owner
            coin['locked'] = buffer[pos]
            pos += 1
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
        st_cursor = cursor
        self.type = struct.unpack("H", buffer[cursor:cursor+2])[0]
        cursor += 2
        self.time = struct.unpack("I", buffer[cursor:cursor+2])[0]
        # self.time = readUint48(buffer, cursor)
        cursor += 4

    async def getHash(self):
        values = await self.serialize(for_hash=True)
        hash_bytes = Coder.hashTwice(values)
        return hash_bytes

    async def parse(self, buffer, cursor=0):
        st_cursor = cursor
        self.type = struct.unpack("H", buffer[cursor:cursor+2])[0]
        cursor += 2
        self.time = struct.unpack("I", buffer[cursor:cursor+2])[0]
        cursor += 4
        st2_cursor = cursor
        pos, self.remark = Coder.readByLength(buffer, cursor, check_size=True)
        cursor += pos
        cursor, self.raw_tx_data = Coder.readByLength(buffer, cursor, check_size=True)
        cursor, self.raw_coin_data = Coder.readByLength(buffer, cursor, check_size=True)
        cursor, self.raw_signature = Coder.readByLength(buffer, cursor, check_size=True)
        self.size = cursor - st_cursor
        return cursor
    
    async def serialize(self, for_hash=False, update_coins=True, update_data=True):
        if update_data:
            self.raw_tx_data = await self._write_data()
        if update_coins:
            self.raw_coin_data = await self._write_coin_data()
            
        output = b""
        output += struct.pack("H", self.type)
        output += struct.pack("I", self.time)
        output += Coder.writeWithLength(self.remark)
        output += Coder.writeWithLength(self.raw_tx_data)
        output += Coder.writeWithLength(self.raw_coin_data)
        if not for_hash:
            output += Coder.writeWithLength(self.raw_signature)
        return output


    async def toDict(self):
        try:
            remark = self.remark and self.remark.decode('utf-8') or None
        except UnicodeDecodeError:
            remark = base64.b64encode(self.remark).decode("utf-8")

        return {
            'hash': str(self.hash),
            'type': self.type,
            'time': self.time,
            'blockHeight': self.height,
            'fee': self.type != 1 and self.coin_data.getFee() or 0,
            'remark': remark,
            'scriptSig': self.scriptSig and self.scriptSig.hex() or None,
            'size': self.size,
            'txData': self.module_data,
            'coinFroms': self.inputs,
            'coinTos': self.outputs
        }

    @staticmethod
    async def fromDict(value):
        item = Transaction()
        item.type = value['type']
        item.time = value.get('time')
        if item.time is None:
            item.time = Coder.timestampFromTime(datetime.now())
        item.height = value.get('height') # optionnal, when creating a tx.
        item.remark = value.get('remark', b'')
        item.scriptSig = value.get('scriptSig')
        item.size = value.get('size')
        item.module_data = value.get('txData') # this should be fixed.
        item.inputs = value.get('coinFroms', [])
        item.outputs = value.get('coinTos', [])
        return item

    async def signTx(self, pri_key):
        self.signature = NulsSignature.signData(pri_key, await self.getHash())
        self.raw_signature = self.signature.serialize()

    async def calculateFee(self):
        size = len(await self.serialize())
        unit_fee = Define.UNIT_FEE
        if self.type in [2, 10, 101]:
            unit_fee = Define.CHEAP_UNIT_FEE
        fee = unit_fee * math.ceil(size / Define.KB)  # per kb
        return fee
    
    