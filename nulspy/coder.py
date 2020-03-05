import struct
import time
from hashlib import sha256

class VarInt:
    """
    public final long value;
    private final int originallyEncodedSize;
    """

    def __init__(self, value=None):
        self.value = value
        self.originallyEncodedSize = 1
        if value is not None:
            self.originallyEncodedSize = self.getSizeInBytes()

    def parse(self, buf, offset):
        first = 0xFF & buf[offset]
        if (first < 253):
            self.value = first
            # 1 data byte (8 bits)
            self.originallyEncodedSize = 1
        elif (first == 253):
            self.value = (0xFF & buf[offset + 1]
                          ) | ((0xFF & buf[offset + 2]) << 8)
            # 1 marker + 2 data bytes (16 bits)
            self.originallyEncodedSize = 3
        elif (first == 254):
            #value = SerializeUtils.readUint32LE(buf, offset + 1)
            self.value = struct.unpack("<I", buf[offset+1:offset+5])[0]
            # 1 marker + 4 data bytes (32 bits)
            self.originallyEncodedSize = 5
        else:
            #value = SerializeUtils.readInt64LE(buf, offset + 1)
            self.value = struct.unpack("<Q", buf[offset+1:offset+9])[0]
            # 1 marker + 8 data bytes (64 bits)
            self.originallyEncodedSize = 9

    def getOriginalSizeInBytes(self):
        return self.originallyEncodedSize

    def getSizeInBytes(self):
        return self.sizeOf(self.value)

    @staticmethod
    def sizeOf(value):
        # if negative, it's actually a very large unsigned long value
        if (value < 0):
            # 1 marker + 8 data bytes
            return 9
        if (value < 253):
            # 1 data byte
            return 1
        if (value <= 0xFFFF):
            # 1 marker + 2 data bytes
            return 3
        if (value <= 0xFFFFFFFF):
            # 1 marker + 4 data bytes
            return 5
        # 1 marker + 8 data bytes
        return 9

    def encode(self):
        """
        Encodes the value into its minimal representation.
        @return the minimal encoded bytes of the value
        """
        ob = bytes()
        size = self.sizeOf(self.value)
        if size == 1:
            return bytes((self.value, ))
        elif size == 3:
            return bytes((253, self.value & 255, self.value >> 8))
        elif size == 5:
            return bytes((254, )) + struct.pack("<I", self.value)
        else:
            return bytes((255, )) + struct.pack("<Q", self.value)
        
def _byte(b):
    return bytes((b, ))

class Coder:
    
    @staticmethod
    def readByLength(buffer, cursor=0, check_size=True):
        if check_size:
            fc = VarInt()
            fc.parse(buffer, cursor)
            length = fc.value
            size = fc.originallyEncodedSize
        else:
            length = buffer[cursor]
            size = 1

        value = buffer[cursor+size:cursor+size+length]
        return (size+length, value)
    
    @staticmethod
    def writeWithLength(buffer):
        if len(buffer) < 253:
            return bytes([len(buffer)]) + buffer
        else:
            return VarInt(len(buffer)).encode() + buffer
    
    @staticmethod
    def timestampFromTime(timedata):
        return int(time.mktime(timedata.timetuple())*1000)
    
    @staticmethod
    def readUint48(buffer, cursor=0):
        value = (buffer[cursor + 0] & 0xff) | \
                ((buffer[cursor + 1] & 0xff) << 8) | \
                ((buffer[cursor + 2] & 0xff) << 16) | \
                ((buffer[cursor + 3] & 0xff) << 24) | \
                ((buffer[cursor + 4] & 0xff) << 32) | \
                ((buffer[cursor + 5] & 0xff) << 40)
        cursor += 6
        if (value == 281474976710655):
            return -1
        return value
    
    @staticmethod
    def writeUint48(val):
        nval = bytes([(0xFF & val),
                    (0xFF & (val >> 8)),
                    (0xFF & (val >> 16)),
                    (0xFF & (val >> 24)),
                    (0xFF & (val >> 32)),
                    (0xFF & (val >> 40))])
        return nval
    
    @staticmethod
    def writeVarInt(number):
        """Pack `number` into varint bytes"""
        buf = b''
        while True:
            towrite = number & 0x7f
            number >>= 7
            if number:
                buf += _byte(towrite | 0x80)
            else:
                buf += _byte(towrite)
                break
        return buf
    
    @staticmethod
    def parseVarint(buffer, cursor):
        fc = VarInt()
        fc.parse(buffer, cursor)
        return (fc.originallyEncodedSize+cursor, fc.value)
    
    @staticmethod
    def writeVarint(value):
        return VarInt(value).encode()
    
    @staticmethod
    def hashTwice(buffer):
        return sha256(sha256(buffer).digest()).digest()
    
    @staticmethod
    def writeUint32(val):
        return bytes([(0xFF & val),
                    (0xFF & (val >> 8)),
                    (0xFF & (val >> 16)),
                    (0xFF & (val >> 24))])

    @staticmethod
    def writeUint64(val):
        return bytes([(0xFF & val),
                    (0xFF & (val >> 8)),
                    (0xFF & (val >> 16)),
                    (0xFF & (val >> 24)),
                    (0xFF & (val >> 32)),
                    (0xFF & (val >> 40)),
                    (0xFF & (val >> 48)),
                    (0xFF & (val >> 56))])
