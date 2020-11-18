from nulspy.coder import Coder
from .register import register_tx_type
from nulspy.base_data import BaseNulsData
from nulspy.define import Define
from nulspy.address import Address
from nulspy.trxs.base import BaseModuleData

import struct
import logging
LOGGER = logging.getLogger('contract_module')


class CreateContractData(BaseModuleData):
    @classmethod
    async def fromBuffer(cls, buffer, cursor=0):
        md = dict()
        md['result'] = None  # This should be populated elsewhere

        md['sender'] = buffer[cursor:cursor + Define.ADDRESS_LENGTH]
        cursor += Define.ADDRESS_LENGTH
        md['sender'] = Address.addressFromHash(md['sender'])

        md['contractAddress'] = buffer[cursor:cursor + Define.ADDRESS_LENGTH]
        cursor += Define.ADDRESS_LENGTH
        md['contractAddress'] = Address.addressFromHash(md['contractAddress'])

        md['value'] = struct.unpack("q", buffer[cursor:cursor + 8])[0]
        cursor += 8
        md['codeLen'] = struct.unpack("I", buffer[cursor:cursor + 4])[0]
        cursor += 4
        pos, md['code'] = Coder.readByLength(buffer, cursor=cursor)
        cursor += pos
        md['code'] = md['code'].hex()

        md['gasLimit'] = struct.unpack("q", buffer[cursor:cursor + 8])[0]
        cursor += 8
        md['price'] = struct.unpack("q", buffer[cursor:cursor + 8])[0]
        cursor += 8
        argslen = int(buffer[cursor])
        cursor += 1
        args = []
        for i in range(argslen):
            arglen = int(buffer[cursor])
            cursor += 1
            arg = []
            for j in range(arglen):
                pos, argcontent = Coder.readByLength(buffer, cursor=cursor)
                cursor += pos
                try:
                    argcontent = argcontent.decode('utf-8')
                except UnicodeDecodeError:
                    LOGGER.warning("Unicode decode error here, passing raw value.")
                arg.append(argcontent)

            args.append(arg)

        md['args'] = args
        return cursor, md

    @classmethod
    async def toBuffer(cls, md):
        output = Address.hashFromAddress(md['sender'])
        output += Address.hashFromAddress(md['contractAddress'])
        output += struct.pack("q", md['value'])
        output += struct.pack("I", md['codeLen'])
        output += Coder.writeWithLength(unhexlify(md['code']))
        output += struct.pack("q", md['gasLimit'])
        output += struct.pack("q", md['price'])
        output += bytes([len(md['args'])])
        for arg in md['args']:
            output += bytes([len(arg)])
            for argitem in arg:
                try:
                    argitem = argitem.encode('utf-8')
                except UnicodeEncodeError:
                    LOGGER.warning("Unicode encode error here, passing raw value.")
                output += Coder.writeWithLength(argitem)
        return output


register_tx_type(15, CreateContractData)


class CallContractData(BaseModuleData):
    @classmethod
    async def fromBuffer(cls, buffer, cursor=0):
        md = dict()
        md['result'] = None  # This should be populated elsewhere

        md['sender'] = buffer[cursor:cursor + Define.ADDRESS_LENGTH]
        cursor += Define.ADDRESS_LENGTH
        md['sender'] = Address.addressFromHash(md['sender'])

        md['contractAddress'] = buffer[cursor:cursor + Define.ADDRESS_LENGTH]
        cursor += Define.ADDRESS_LENGTH
        md['contractAddress'] = Address.addressFromHash(md['contractAddress'])

        # TODO: change value to 256bit bigint
        md['value'] = struct.unpack("q", buffer[cursor:cursor + 8])[0]
        cursor += 8
        md['gasLimit'] = struct.unpack("q", buffer[cursor:cursor + 8])[0]
        cursor += 8
        md['price'] = struct.unpack("q", buffer[cursor:cursor + 8])[0]
        cursor += 8

        pos, md['methodName'] = Coder.readByLength(buffer, cursor=cursor)
        md['methodName'] = md['methodName'].decode('utf-8')
        cursor += pos
        pos, md['methodDesc'] = Coder.readByLength(buffer, cursor=cursor)
        md['methodDesc'] = md['methodDesc'].decode('utf-8')
        cursor += pos
        argslen = int(buffer[cursor])
        cursor += 1
        args = []
        for i in range(argslen):
            arglen = int(buffer[cursor])
            cursor += 1
            arg = []
            for j in range(arglen):
                pos, argcontent = Coder.readByLength(buffer, cursor=cursor)
                cursor += pos
                try:
                    argcontent = argcontent.decode('utf-8')
                except UnicodeDecodeError:
                    LOGGER.warning("Unicode decode error here, passing raw value.")
                arg.append(argcontent)

            args.append(arg)

        md['args'] = args
        return cursor, md

    @classmethod
    async def toBuffer(cls, md):
        output = Address.hashFromAddress(md['sender'])
        output += Address.hashFromAddress(md['contractAddress'])
        output += md['value'].to_bytes(32, 'little')
        output += struct.pack("Q", md['gasLimit'])
        output += struct.pack("Q", md['price'])
        output += Coder.writeWithLength(md['methodName'].encode('utf-8'))
        output += Coder.writeWithLength(md['methodDesc'].encode('utf-8'))
        output += bytes([len(md['args'])])
        for arg in md['args']:
            output += bytes([len(arg)])
            for argitem in arg:
                try:
                    argitem = argitem.encode('utf-8')
                except UnicodeEncodeError:
                    LOGGER.warning("Unicode encode error here, passing raw value.")
                output += Coder.writeWithLength(argitem)
        return output


register_tx_type(16, CallContractData)


class DeleteContractData(BaseModuleData):
    @classmethod
    async def fromBuffer(cls, buffer, cursor=0):
        md = dict()
        md['result'] = None  # This should be populated elsewhere

        md['sender'] = buffer[cursor:cursor + Define.ADDRESS_LENGTH]
        cursor += Define.ADDRESS_LENGTH
        md['sender'] = Address.addressFromHash(md['sender'])

        md['contractAddress'] = buffer[cursor:cursor + Define.ADDRESS_LENGTH]
        cursor += Define.ADDRESS_LENGTH
        md['contractAddress'] = Address.addressFromHash(md['contractAddress'])
        return cursor, md

    @classmethod
    async def toBuffer(cls, md):
        output = Address.hashFromAddress(md['sender'])
        output += Address.hashFromAddress(md['contractAddress'])
        return output


register_tx_type(17, DeleteContractData)