class BaseModuleData:
    def __init__(self, data_dict=None, data=None):
        self._data = dict()
        if data_dict is not None:
            self._data = data_dict

    @staticmethod
    async def fromBuffer(buffer, cursor=0):
        raise NotImplementedError

    @staticmethod
    async def toBuffer(data):
        raise NotImplementedError

    async def parse(self, data, cursor=0):
        self._data, cursor = await self.fromBuffer(data, cursor=cursor)
        return cursor

    async def serialize(self):
        return await self.toBuffer(self._data)

    @staticmethod
    async def fromDict(data):
        c = BaseModuleData(data_dict=data)

    async def toDict(self):
        return self._data