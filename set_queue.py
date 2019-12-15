from queue import Queue, Empty
from echonet_lite import Object, Frame, Node, Property
import logging
logger = logging.getLogger(__name__)

class SetQueue(Queue):
    def __init__(self):
        super().__init__()
        self._keys = set()

    def generateKey(self, item):
        if type(item) == Frame:
            key = []
            for p in item.properties:
                key.append(p.EPC)
            return tuple(key)
        else:
            return None

    def put(self, item, block=True, timeout=None):
        key = self.generateKey(item)
        if key is None:
            return 
        if key not in self._keys:
            self._keys.add(key)
            super().put(item, block, timeout)
            logger.info(self._keys)

    def get(self, block=True, timeout=None):
        item = super().get(block,timeout)
        self._keys.remove(self.generateKey(item))
        return item