# coding: utf-8
from threading import Thread
from echonet_lite import Frame
import time
import binascii
from queue import Queue, Empty
from wisun_manager import WisunManager
from logging import getLogger

logger = getLogger(__name__)


class WisunManager(WisunManager):
    scan_cmd_c0 = "SKSCAN 2 FFFFFFFF 6 0\r\n"
    scan_cmd_a1 = "SKSCAN 2 FFFFFFFF 6\r\n"
    sendto_cmd_c0 = "SKSENDTO 1 {0} 0E1A 1 0 {1:04X} "
    sendto_cmd_a1 = "SKSENDTO 1 {0} 0E1A 1 {1:04X} "

    def __init__(self, pwd, bid, ser):
        super().__init__(pwd, bid, ser)
        self._connected = False
        self._scan_cmd = self.scan_cmd_c0
        self._sendto_cmd = self.sendto_cmd_c0

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
            if line.startswith(b"ERXUDP"):
                cols = line.split(b" ")
                port = int(cols[4], 16)
                if port == 3610:
                    # echonet lite frame
                    if len(cols) > 9:
                        length = int(cols[8], 16)
                        bar = bytearray(binascii.a2b_hex(cols[9][0 : length * 2]))
                    else:
                        length = int(cols[7], 16)
                        bar = bytearray(binascii.a2b_hex(cols[8][0 : length * 2]))
                    frame = Frame(bar)
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
            command = self._sendto_cmd.format(self._ipv6Addr, len(payload))
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
        # if self._setOpt() is False:
        #     return False
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
            if self._sendAndWaitOk(self._scan_cmd.encode("utf-8")) == False:
                logger.info("switch BP35A1 mode")
                self._scan_cmd = self.scan_cmd_a1
                self._sendto_cmd = self.sendto_cmd_a1
                continue

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
        authRetry = 12  # 5 min * 12 = 1 hour
        # 接続完了待ち
        while True:
            # line = self._serialReceiveLine()
            try:
                line = self._queueRecv.get(True, 30)
                if line.startswith(b"EVENT 24"):
                    # 認証失敗 -> 再認証
                    if authRetry < 1:
                        return False
                    authRetry = authRetry - 1
                    logger.info("認証失敗のため 300 秒後に再認証開始")
                    time.sleep(300)
                    self._serialSendLine(
                        "SKJOIN {0}\r\n".format(ipv6Addr.decode()).encode()
                    )
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
