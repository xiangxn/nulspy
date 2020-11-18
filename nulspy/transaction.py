import struct
import math
from .define import Define
from .coder import Coder, VarInt
from .address import Address
from .base_data import BaseNulsData
from .data import NulsDigestData
from .signature import NulsSignature
from .trxs.register import TX_TYPES_REGISTER

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
    
    