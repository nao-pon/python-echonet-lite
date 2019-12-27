# coding: utf-8
from threading import Event, Thread
from echonet_lite import Object, Frame, Node, Property
import serial
from time import sleep
from queue import Queue, Empty
import struct
from wisun_manager import WisunManager, ComError
from logging import getLogger, StreamHandler, INFO, Formatter
logger = getLogger(__name__)

# Constants
# Unique Code
UNQ_REQ = b'\xd0\xea\x83\xfc'
UNQ_RES = b'\xd0\xf9\xee\x5d'
UNQ_INF = b'\xd0\xf9\xee\x5d'
# Dual Mode
# Command Code
CMD_GET_STATUS = 0x0001
CMD_GET_UDP = 0x0007
CMD_GET_IP = 0x0009
CMD_GET_MAC = 0x000e
CMD_GET_CONNECT = 0x0011
CMD_GET_TERMINAL = 0x0100
CMD_GET_NEIGHBOR_DIS = 0x0102
CMD_GET_INITIAL = 0x0107
CMD_GET_UART = 0x010b
CMD_INITIALIZE = 0x005f
CMD_SET_NEIGHBOR_DIS = 0x0101
CMD_SET_UART = 0x010a
CMD_UDP_OPEN = 0x0005
CMD_UDP_CLOSE = 0x0006
CMD_SEND_DATA = 0x0008
CMD_ACTIVE_SCAN = 0x0051
CMD_SEND_PING = 0x00d1
CMD_ED_SCAN = 0x00db
CMD_GET_VERSION = 0x006b
CMD_HW_RESET = 0x00d9
CMD_WRITE_MODE = 0x00f0
CMD_B_ROUTE_GET_ENCRYPTION_KEY = 0x0059
CMD_B_ROUTE_GET_PANID = 0x005e
CMD_B_ROUTE_SET_PANA_INFO = 0x0054
CMD_B_ROUTE_START = 0x0053
CMD_B_ROUTE_PANA_START = 0x0056
CMD_B_ROUTE_PANA_END = 0x0057
CMD_B_ROUTE_END = 0x0058
CMD_B_ROUTE_PANA_RE_AUTH = 0x00d2
# Response Code
RES_GET_STATUS = 0x2001
RES_GET_UDP = 0x2007
RES_GET_IP = 0x2009
RES_GET_MAC = 0x200e
RES_GET_CONNECT = 0x2011
RES_GET_TERMINAL = 0x2100
RES_GET_NEIGHBOR_DIS = 0x2102
RES_GET_INITIAL = 0x2107
RES_GET_UART = 0x210b
RES_INITIALIZE = 0x205f
RES_SET_NEIGHBOR_DIS = 0x2101
RES_SET_UART = 0x210a
RES_UDP_OPEN = 0x2005
RES_UDP_CLOSE = 0x2006
RES_SEND_DATA = 0x2008
RES_ACTIVE_SCAN = 0x2051
RES_SEND_PING = 0x20d1
RES_ED_SCAN = 0x20db
RES_GET_VERSION = 0x206b
RES_WRITE_MODE = 0x20f0
RES_B_ROUTE_GET_ENCRYPTION_KEY = 0x2059
RES_B_ROUTE_GET_PANID = 0x205e
RES_B_ROUTE_SET_PANA_INFO = 0x2054
RES_B_ROUTE_START = 0x2053
RES_B_ROUTE_PANA_START = 0x2056
RES_B_ROUTE_PANA_END = 0x2057
RES_B_ROUTE_END = 0x2058
RES_B_ROUTE_PANA_RE_AUTH = 0x20d2
# Information Code
INF_ACTIVE_SCAN = 0x4051
INF_SEND_PING = 0x60d1
INF_RECV_DATA = 0x6018
INF_BOOTED = 0x6019
INF_CHANGE_CONNECT_STATE = 0x601a
INF_PANA_AUTH = 0x6028
INF_RECV_ERROR = 0x6038
# Receive State
RCV_IDLE = 0
RCV_HEADER = 1
RCV_DATA = 2


class WisunManager(WisunManager):
    def __init__(self, pwd, bid, dev):
        super().__init__(pwd, bid, dev)
        self._smartmeterCh = None
        self._connected = False

    # モジュール有効状態チェック
    def isActive(self):
        return self._getVersion()

    def _dump(self, data):
        return [hex(i) for i in data]

    # Wi-SUN経由Echonet送信
    def wisunSendFrame(self, frame: Frame):
        if self._ipv6Addr is not None:
            # print('send: {0}'.format(frame))
            payload = frame.get_bytes()
            data_len = len(payload)
            cmd = struct.pack('>8sQHHH{0}s'.format(data_len), b'\xfe\x80\x00\x00\x00\x00\x00\x00',
                              self._ipv6Addr ^ 0x0200000000000000, 3610, 3610, data_len, payload)
            self.sendReq(CMD_SEND_DATA, cmd)

    # 要求コマンド送信
    def sendReq(self, cmd, data):
        self._clearReceiveQueue()
        logger.info('send req: {0:04X}'.format(cmd))
        data_len = len(data)
        buf = struct.pack('>4sHH', UNQ_REQ, cmd, data_len + 4)
        hs = sum(buf)
        buf = struct.pack('>{0}sHH{1}s'.format(
            len(buf), data_len), buf, hs, sum(data), data)
        logger.debug(self._dump(buf))
        self._serialSendLine(buf)

    # 受信タスク開始
    def startReceiveTask(self):
        self._queueRecv = Queue()
        self._stopReceiveEvent = False
        self._rcvThread = Thread(
            target=self._recvTask, args=(self._queueRecv,))
        self._rcvThread.start()

    # 受信タスク終了
    def stopReceiveTask(self):
        self._stopReceiveEvent = True
        self._rcvThread.join()

    # WiSUN受信タスク
    def _recvTask(self, queue):
        logger.info('receive task start')
        bar = bytearray()
        state = (RCV_IDLE, 1)
        header_sum = 0
        while not self._stopReceiveEvent:
            dt = self._serialReceive(state[1])
            if len(dt) < state[1]:
                state = (RCV_IDLE, 1)
            else:
                # print('state({0}) : dt({1})'.format(state, self._dump(dt)))
                # bar.append(dt[0])
                bar += dt
                # logger.info(bar)
                if state[0] == RCV_IDLE:
                    # ユニークコードをハント
                    if len(bar) == 4:
                        if bar.startswith(UNQ_RES):
                            logger.info('unique: {0}'.format(self._dump(bar)))
                            header_sum = sum(bar)
                            bar.clear()
                            state = (RCV_HEADER, 8)
                        else:
                            bar = bar[1:]
                elif state[0] == RCV_HEADER:
                    # 8byte読み込み
                    header_sum += sum(bar[0:4])
                    values = struct.unpack('>HHHH', bar)
                    logger.info("header: {0}".format(self._dump(values)))
                    command = values[0]
                    data_len = values[1] - 4
                    check_header = values[2]
                    check_data = values[3]
                    logger.debug('check:{0:04x}, sum:{1:04x}'.format(
                        check_header, header_sum))
                    if check_header == header_sum and data_len > 0:
                        logger.debug('header sum check ok')
                        logger.debug('data len={0}'.format(data_len))
                        data_sum = 0
                        state = (RCV_DATA, data_len)
                    else:
                        state = (RCV_IDLE, 1)
                    bar.clear()
                elif state[0] == RCV_DATA:
                    logger.info('data: {0}'.format(self._dump(bar)))
                    data_sum = sum(bar)
                    logger.debug('check:{0:04x}, sum:{1:04x}'.format(
                        check_data, data_sum))
                    if check_data == data_sum:
                        logger.debug('data sum check ok')
                        data = b'' + bar
                        if command == INF_RECV_DATA:
                            head_len = 16 + 2 + 2 + 2 + 1 + 1 + 1 + 2
                            frames = struct.unpack(
                                '>16sHHHbbbH', bar[0:head_len])
                            ipAddr = frames[0]
                            srcPort = frames[1]
                            dstPort = frames[2]
                            panId = frames[3]
                            addrType = frames[4]
                            encryption = frames[5]
                            rssi = frames[6]
                            data_len = frames[7]
                            logger.info('{0}, srcPort*{1}, dstPort={2}, panId={3}, addrType={4}, encryption={5}, rssi={6}dBm, len={7}byte'.format(
                                ipAddr, srcPort, dstPort, panId, addrType, encryption, rssi, data_len))
                            frame = Frame(bar[head_len:head_len+data_len])
                            self.putProperty(frame)
                        else:
                            queue.put((command, data))
                    state = (RCV_IDLE, 1)
                    bar.clear()
        logger.info('receive task end')

    def _waitOk(self, message, wait_cmd):
        try:
            response = self._queueRecv.get(True, 10)
            cmd = response[0]
            res = response[1]
            logger.info('waitOk: {0}'.format(res))
            if cmd == wait_cmd and res[0] == 0x01:
                return True
            else:
                logger.warning(message)
                return False
        except Empty:
            logger.warning('timeout({0})'.format(message))
            return False

    def _getVersion(self):
        # バージョン取得
        self.sendReq(CMD_GET_VERSION, b'')
        return self._waitOk('CMD_GET_VERSION error', RES_GET_VERSION)

    def _initialize(self, ch):
        # 初期設定
        # Dual mode, HAN Sleep 無効, チャネル４, 20mW
        self.sendReq(CMD_INITIALIZE, struct.pack('BBBB', 0x05, 0x00, ch, 0x00))
        return self._waitOk('CMD_INITIALIZE error', RES_INITIALIZE)

    def _activeScan(self):
        retry = 3
        values = False
        for i in range(retry):
            # アクティブスキャン実行
            # scan 5s, scan ch4-17, PairingIDあり, PairingID(bid last8byte)
            self.sendReq(CMD_ACTIVE_SCAN, b'\x09\x00\x03\xff\xf0\x01' +
                         self._bid.encode()[-8:])
            # self.sendReq(CMD_ACTIVE_SCAN, b'\x0a\x00\x02\x00\x00\x01' + self._bid.encode()[-8:]) # scan 5s, scan ch17, PairingIDあり, PairingID(bid last8byte)
            while True:
                try:
                    response = self._queueRecv.get(True, 10)
                    cmd = response[0]
                    res = response[1]
                    if cmd == RES_ACTIVE_SCAN:
                        if len(res) == 1 and res[0] == 0x01:
                            # 完了
                            break
                    elif cmd == INF_ACTIVE_SCAN:
                        if len(res) == 2 and res[0] == 0x01:
                            # 応答なし
                            logger.info('ch{0} is no response'.format(res[1]))
                        elif len(res) > 2 and res[0] == 0x00:
                            # 応答あり
                            values = struct.unpack_from('>BBQHb', res, 1)
                            ch = values[0]
                            count = values[1]
                            mac = values[2]
                            panId = values[3]
                            rssi = values[4]
                            logger.info('ch{0} ,mac={1:016x}, panId={2:04x}, rssi={3}'.format(
                                ch, mac, panId, rssi))
                        else:
                            logger.warning('CMD_ACTIVE_SCAN error')
                            values = False
                            break
                except Empty:
                    values = False
                    break
            if values is not False:
                break
            else:
                # retry
                sleep(2.0)
        return values

    def _setBrouteParameter(self):
        # BルートPANA認証情報設定
        self.sendReq(CMD_B_ROUTE_SET_PANA_INFO, struct.pack('{0}s{1}s'.format(
            len(self._bid), len(self._pwd)), self._bid.encode(), self._pwd.encode()))
        return self._waitOk('CMD_B_ROUTE_SET_PANA_INFO error', RES_B_ROUTE_SET_PANA_INFO)

    def _startBroute(self):
        # Bルート動作開始
        retry = 3
        for i in range(retry):
            self.sendReq(CMD_B_ROUTE_START, b'')
            try:
                response = self._queueRecv.get(True, 3)
                res = response[1]
                if len(res) == 13:
                    # 応答あり
                    values = struct.unpack('>BBHQb', res)
                    res = values[0]
                    ch = values[1]
                    panId = values[2]
                    mac = values[3]
                    self._ipv6Addr = mac
                    rssi = values[4]
                    logger.info('ch{0} ,mac={1:016x}, panId={2:04x}, rssi={3}'.format(
                        ch, mac, panId, rssi))
                    return values
                else:
                    logger.warning('CMD_B_ROUTE_START error')
            except Empty:
                return values
            # retry
            sleep(2.0)
        return False

    def _stopBroute(self):
        retry = 3
        for i in range(retry):
            # Bルート動作終了
            self.sendReq(CMD_B_ROUTE_END, b'')
            if self._waitOk('CMD_B_ROUTE_END error', RES_B_ROUTE_END):
                return True
            # retry
            sleep(2.0)
            return False

    def _startBroutePANA(self):
        retry = 3
        for i in range(retry):
                # BルートPANA開始
            self.sendReq(CMD_B_ROUTE_PANA_START, b'')
            if self._waitOk('CMD_B_ROUTE_PANA_START error', RES_B_ROUTE_PANA_START):
                            # try:
                            # response = self._queueRecv.get(True, 10)
                            # cmd = response[0]
                            # res = response[1]
                            # logger.info('waitOk: {0}'.format(res))
                            # if cmd == wait_cmd and res[0] == 0x01:
                            #     return True
                            # else:
                            #     logger.warning(message)
                            #     return False
                return True
            # retry
            sleep(2.0)
        return False

    def _stopBroutePANA(self):
        retry = 3
        for i in range(retry):
            # BルートPANA終了
            self.sendReq(CMD_B_ROUTE_PANA_END, b'')
            if self._waitOk('CMD_B_ROUTE_PANA_END error', RES_B_ROUTE_PANA_END):
                return True
            # retry
            sleep(2.0)
        return False

    def _startUdp(self, port):
        retry = 3
        for i in range(retry):
            # UDPポートOPEN
            self.sendReq(CMD_UDP_OPEN, struct.pack('>H', port))
            if self._waitOk('CMD_UDP_OPEN error', RES_UDP_OPEN):
                return True
            # retry
            sleep(2.0)
        return False

    def _stopUdp(self, port):
        retry = 3
        for i in range(retry):
            # UDPポートCLOSE
            self.sendReq(CMD_UDP_CLOSE, struct.pack('>H', port))
            if self._waitOk('CMD_UDP_CLOSE error', RES_UDP_CLOSE):
                return True
            # retry
            sleep(2.0)
        return False

    def _reauthenticationBroutePANA(self):
        retry = 3
        for i in range(retry):
            # BルートPANA再認証
            self.sendReq(CMD_B_ROUTE_PANA_RE_AUTH, b'')
            if self._waitOk('CMD_B_ROUTE_PANA_RE_AUTH error', RES_B_ROUTE_PANA_RE_AUTH):
                return True
            # retry
            sleep(2.0)
        return False

    # スマートメーター接続
    def connect(self):
        self._connected = False
        try:
            if self._smartmeterCh is None:
                # 初期化（任意チャネル）
                if not self._initialize(4):
                    raise ComError('Initialize1')
                sleep(0.2)
                # アクティブスキャン
                values = self._activeScan()
                if values is False:
                    raise ComError('Active Scan')
                self._smartmeterCh = values[0]
            # 初期化（任意チャネル）
            if not self._initialize(self._smartmeterCh):
                raise ComError('Initialize2')
            sleep(0.2)
            # BルートPANA認証情報設定
            if not self._setBrouteParameter():
                raise ComError('B route PANA Setting')
            # Bルート動作開始
            values = self._startBroute()
            if values is False:
                raise ComError('B route Start')
            # UDPポートOPEN
            port = 3610
            if not self._startUdp(port):
                raise ComError('UDP({0}) open'.format(port))
            # BルートPANA開始
            if not self._startBroutePANA():
                raise ComError('B route PANA Start')
            # 送信タスク開始
            self.startSendTask()
            self._connected = True
        except ComError as err:
            logger.warning('{0} error'.format(err))
            self.reset()
        finally:
            return self._connected

    # スマートメーター切断
    def disconnect(self):
        if not self._connected:
            return
        try:
            # 送信タスク終了
            self.stopSendTask()
            # BルートPANA終了
            if not self._stopBroutePANA():
                raise ComError('B route PANA Stop')
            # UDPポートCLOSE
            port = 3610
            if not self._stopUdp(port):
                raise ComError('UDP({0}) close'.format(port))
            # Bルート動作終了
            if not self._stopBroute():
                raise ComError('B route Stop')
            # HWリセット
            self.reset()
            sleep(3.0)
        except ComError as err:
            logger.warning('{0} error'.format(err))
            self.reset()
            return
        finally:
            self._connected = False


if __name__ == '__main__':
    wm = None
    try:
        wm = WisunManager()
        wm.reset()

        while True:
            sleep(1)
    except KeyboardInterrupt:
        if wm is not None:
            wm.close()
