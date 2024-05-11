# coding: utf-8
from dgbox_led import DGboxLed
from wisun_manager_factory import WisunManagerFactory
from ethernet_manager import EthernetManager
from property_manager import PropertyManager
from logging import getLogger, StreamHandler, INFO, Formatter, DEBUG
import time
from time import sleep
from enum import Enum
from threading import Thread
import signal
import sys

# ログの設定
handler = StreamHandler()
handler.setLevel(DEBUG)
handler.setFormatter(
    Formatter("[%(asctime)s] [%(levelname)s] [%(threadName)s] [%(name)s] %(message)s")
)
logger = getLogger()
logger.addHandler(handler)
logger.setLevel(INFO)

# On-bord LEDs
boxled = DGboxLed()
# Wi-SUNマネージャ
wm = WisunManagerFactory.createInstance()
wm.setBoxled(boxled)
# Ethernetマネージャ
em = EthernetManager()
# Propertyマネージャ
pm = PropertyManager()
pm.setWisunManager(wm)
pm.setEthernetManager(em)


class ConnectState(Enum):
    DISCONNECT = 0
    CONNECTING = 1
    CONNECTED = 2
    INITIALIZING = 3
    ACQUIRING = 4
    READY = 5
    CONNECT_ERROR = 6
    DEVICE_ERROR = 7


thread = None
if wm is None:
    connect_state = ConnectState.DEVICE_ERROR
else:
    connect_state = ConnectState.DISCONNECT

wm.setConnectState(connect_state)


def main():
    global thread
    global connect_state

    signal.signal(signal.SIGTERM, termed)

    # EthernetベースのEchonet処理開始
    em.start()
    while em._node is None:
        time.sleep(0.1)

    pre_state = connect_state

    # 電源投入時にWi-SUN自動接続
    startConnect()

    while True:
        wm.setConnectState(connect_state)
        _conState = connect_state
        if _conState == ConnectState.CONNECT_ERROR:
            logger.info("再接続まで 3600 秒待ちます")
            time.sleep(3600)
        if (
            wm is not None
            and wm._lastPutTime is not None
            and wm._lastPutTime + 300 < time.time()
        ) or _conState == ConnectState.CONNECT_ERROR:
            wm.disconnect()
            startConnect()
            _conState = connect_state

        if _conState == ConnectState.CONNECTED:
            # Wi-SUN manager の初期リクエストフラグ設定
            wm._initReq = True
            _conState = connect_state = ConnectState.INITIALIZING
            boxled.off(4)
        if _conState == ConnectState.INITIALIZING:
            # 初期リクエストでメーカーコードがキャッシュされるのを待つ
            unit = pm._cache.get(0xE1)  # 積算電力量単位（正方向、逆方向計測値）
            mcode = pm._cache.get(0x8A)  # メーカーコード
            if unit is not None and mcode is not None:
                if len(mcode.EDT):
                    # echonet_lite/__init__.py の Node _mcode プロパティへ設定
                    em._node._mcode = mcode.EDT
                if len(unit.EDT):  # 積算電力量単位は必須
                    wm._initReq = False
                    _conState = connect_state = ConnectState.ACQUIRING
                    boxled.off(3)
        if _conState == ConnectState.ACQUIRING:
            if pm._cache.get(0xE7) is not None:
                _conState = connect_state = ConnectState.READY
                boxled.off(2)

        pre_state = connect_state

        time.sleep(0.1)


# Wi-SUN接続タスク起動


def startConnect():
    if wm is None:
        return
    global thread
    global connect_state
    boxled.on(2)
    boxled.on(3)
    boxled.on(4)
    connect_state = ConnectState.CONNECTING
    thread = Thread(target=connect_task)
    thread.start()


# Wi-SUN接続タスク


def connect_task():
    global thread
    global connect_state
    # スマートメータ接続
    logger.info("接続開始")
    connected = wm.connect()
    if connected:
        logger.info("接続成功")
        connect_state = ConnectState.CONNECTED
    else:
        logger.info("接続失敗")
        connect_state = ConnectState.CONNECT_ERROR
    thread = None


def dispose():
    # EthernetベースのEchonet処理終了
    em.stop()
    # スマートメータ切断
    if wm is not None:
        wm.disconnect()
        wm.dispose()
    boxled.clear()


def termed(signum, frame):
    logger.info("SIGTERM!")
    dispose()
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt")
        dispose()
