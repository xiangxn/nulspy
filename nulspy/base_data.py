from .define import Define


class BaseNulsData:
    def _pre_parse(buffer, cursor=None, length=None):
        if cursor is not None:
            buffer = buffer[cursor:]
        if length is not None:
            buffer = buffer[:length]
        if (bytes is None) or (len(bytes) == 0) or (len(bytes) == 4) or (bytes == Define.PLACE_HOLDER):
            return

    def _prepare(self, item):
        if item is None:
            return Define.PLACE_HOLDER
        else:
            return item.serialize()
        

