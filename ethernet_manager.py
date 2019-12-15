# coding: utf-8
import time
from echonet_lite import Object, Frame, Node, Property
from threading import Event, Thread
from logging import getLogger, StreamHandler, INFO, Formatter
logger = getLogger(__name__)
logger.setLevel(INFO)


class EthernetManager(Object):
    ''' SmartMeter Object (group=0x02, class=0x88) '''
    # リクエストID
    # requestId = 0

    def __init__(self):
        Object.__init__(self, 0x02, 0x88)
        self._recAddr = {}
        self._propMan = None
        self._Thread = None
        self._node = None

    # Propertyマネージャ設定
    def setPropertyManager(self, pm):
        self._propMan = pm

    # Ethernet処理タスク開始
    def start(self):
        self._stopReceiveEvent = False
        self._Thread = Thread(target=self._task)
        self._Thread.start()

    # Ethernet処理タスク終了
    def stop(self):
        if self._Thread is None:
            return
        self._stopReceiveEvent = True
        self._Thread.join()

    # Ethernet処理タスク        
    def _task(self):
        logger.info('receive task start')
        # EthernetベースのEchonet開始
        self._node = Node()
        self._node.add_object(self)
        while not self._stopReceiveEvent:
            self._node.recvfrom()
        # node.loop()
        logger.info('receive task end')

    # Echonet受信
    def service(self, frame, addr):
        logger.info(frame)
        if frame.ESV == 0x62 and self._propMan is not None:  # Get
            new_frame = self._propMan.get(frame)
            if type(new_frame) is Frame:
                logger.info(
                    "EthernetManager.service cached :{0}".format(new_frame))
                # PropertyManagerにキャッシュ済み
                if len(new_frame.properties) == 0:
                    time.sleep(5.0)
                return new_frame
            else:
                logger.info(
                    "EthernetManager.service request:{0}".format(new_frame))
                # PropertyManagerに未キャッシュ
                # self._recAddr[EthernetManager.requestId] = addr
                self._recAddr[new_frame] = addr
                # self._propMan.get(frame, EthernetManager.requestId)
                # EthernetManager.requestId += 1
        return None

    # Echonet送信（応答）
    def sendResponse(self, frame, key):
        # addr = self._recAddr[requestId]
        if key in self._recAddr:
            logger.info("EthernetManager.sendResponse :{0}".format(frame))
            addr = self._recAddr[key]
            if self._node is not None:
                self._node.sendto(frame.get_bytes(), (addr[0], 3610))

    # Echonet送信（通知）
    def sendNotification(self, frame):
        if self._node is not None:
            self._node.sendto(frame.get_bytes(), ('224.0.23.0', 3610))


if __name__ == '__main__':
    try:
        logger.info('EthernetManager start')
        em = EthernetManager()
        node = Node()
        node.add_object(em)
        node.loop()
    except KeyboardInterrupt:
        pass
