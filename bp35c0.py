# coding: utf-8
from gpiozero import LED
from threading import Event, Thread
from echonet_lite import Object, Frame, Node, Property
import serial
import time
import binascii
from queue import Queue, Empty
from configparser import ConfigParser
from wisun_manager import WisunManager
from logging import getLogger, StreamHandler, INFO, Formatter

logger = getLogger(__name__)


class WisunManager(WisunManager):
    def __init__(self, pwd, bid, ser):
        super().__init__(pwd, bid, ser)
        self._connected = False

    # モジュール有効状態チェック
    def isActive(self):
        return self._sendAndWaitOk(b"SKVER\r\n")

    def _sendAndWaitOk(self, statement):
        if self._serialSendLine(statement) is False:
            return False
        return self._waitOk(statement)

    def _waitOk(self, message):
        # print('wait ok start')
        while True:
            try:
                rd = self._queueRecv.get(True, 1)
                if rd.startswith(b"OK"):
                    # print('wait ok end')
                    return True
            except Empty:
                logger.warning("timeout({0})".format(message))
                return False

    def startReceiveTask(self):
        self._queueRecv = Queue()
        self._stopReceiveEvent = False
        self._rcvThread = Thread(target=self._recvTask, args=(self._queueRecv,))
        self._rcvThread.start()

    def stopReceiveTask(self):
        if self._rcvThread is None:
            return
        self._stopReceiveEvent = True
        self._rcvThread.join()

    # WiSUN受信タスク
    def _recvTask(self, queue):
        logger.info("receive task start")
        while not self._stopReceiveEvent:
            line = self._serialReceiveLine()
            if line == b"":
                # timeout
                continue
            logger.info(line)
            if line.startswith(b"ERXUDP"):
                cols = line.split(b" ")
                port = int(cols[4], 16)
                if port == 3610:
                    # echonet lite frame
                    len = int(cols[8], 16)
                    # bar = bytearray(cols[9][0:len])
                    bar = bytearray(binascii.a2b_hex(cols[9][0 : len * 2]))
                    # logger.info(bar)
                    frame = Frame(bar)
                    # logger.info(frame)
                    self.putProperty(frame)
            elif line.startswith(b"EVENT 29"):
                self.sendPause(True)
                if not self._connected:
                    queue.put(line)
            elif line.startswith(b"EVENT 25"):
                self.sendPause(False)
                if not self._connected:
                    queue.put(line)
            else:
                if not self._connected:
                    queue.put(line)
        logger.info("receive task end")

    # Wi-SUN経由Echonet送信
    def wisunSendFrame(self, frame: Frame):
        if self._ipv6Addr is not None:
            # print('send: {0}'.format(frame))
            payload = frame.get_bytes()
            command = "SKSENDTO 1 {0} 0E1A 1 0 {1:04X} ".format(
                self._ipv6Addr, len(payload)
            )
            self._serialSendLine(command.encode())
            self._serialSendLine(payload)
            self._serialSendLine(b"\r\n")
            logger.info(command.encode())
            logger.info(payload)

    # Wi-SUN切断
    def disconnect(self):
        # 送信タスク終了
        self.stopSendTask()
        self._serialSendLine(b"SKTERM\r\n")
        time.sleep(3.0)
        self._clearReceiveQueue()
        self._connected = False

    # プロダクト設定（受信電文16進ASCII）
    def _setOpt(self):
        for i in range(3):
            if self._serialSendLine(b"ROPT\r\n") is False:
                return False
            while True:
                try:
                    rd = self._queueRecv.get(True, 3)
                    if rd.startswith(b"OK 01"):
                        return True
                except Empty:
                    if self._serialSendLine(b"WOPT 01\r\n") is False:
                        return False
                    break
        return False

    # Wi-SUN接続
    def connect(self):
        self.disconnect()
        if self._sendAndWaitOk(b"SKVER\r\n") is False:
            return False
        if self._sendAndWaitOk(b"SKINFO\r\n") is False:
            return False
        if self._sendAndWaitOk(b"SKSREG SFE 0\r\n") is False:
            return False
        if self._setOpt() is False:
            return False
        if (
            self._sendAndWaitOk("SKSETPWD C {0}\r\n".format(self._pwd).encode())
            is False
        ):
            return False
        if self._sendAndWaitOk("SKSETRBID {0}\r\n".format(self._bid).encode()) is False:
            return False
        scanRes = {}
        flag = True
        while flag:
            self._sendAndWaitOk(b"SKSCAN 2 FFFFFFFF 6 0\r\n")
            start = time.time()
            while True:
                # line = self._serialReceiveLine()
                line = self._queueRecv.get()
                if line.startswith(b"EVENT 22"):
                    try:
                        print(scanRes["Channel"])
                        print(scanRes["Pan ID"])
                        print(scanRes["Addr"])
                        flag = False
                        break
                    except KeyError:
                        # EPANDESC受信完了前にEVENT22
                        # print(scanRes)
                        time.sleep(1.0)
                        break
                elif line.startswith(b"  "):
                    cols = line.strip().split(b":")
                    scanRes[cols[0].decode()] = cols[1].decode()
                if time.time() - start > 60:
                    # 60秒間EVENT22なし
                    # print('timeout!')
                    break
        self._sendAndWaitOk("SKSREG S2 {0}\r\n".format(scanRes["Channel"]).encode())
        self._sendAndWaitOk("SKSREG S3 {0}\r\n".format(scanRes["Pan ID"]).encode())
        self._serialSendLine("SKLL64 {0}\r\n".format(scanRes["Addr"]).encode())
        while True:
            # line = self._serialReceiveLine()
            line = self._queueRecv.get()
            if not line.startswith(b"SKLL64"):
                ipv6Addr = line.strip()
                break
        self._serialSendLine("SKJOIN {0}\r\n".format(ipv6Addr.decode()).encode())
        # 接続完了待ち
        while True:
            # line = self._serialReceiveLine()
            try:
                line = self._queueRecv.get(True, 30)
                if line.startswith(b"EVENT 24"):
                    break
                elif line.startswith(b"EVENT 25"):
                    break
            except Empty:
                return False
        self._ipv6Addr = ipv6Addr.decode()
        self.startSendTask()
        self._connected = True
        return True


if __name__ == "__main__":
    try:
        wm = WisunManager()
        wm.connect()

        while True:
            time.sleep(10.0)
    except KeyboardInterrupt:
        wm.disconnect()
        wm.dispose()
