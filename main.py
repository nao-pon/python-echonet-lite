# coding: utf-8
from echonet_lite import Node
from wisun_manager_factory import WisunManagerFactory
from ethernet_manager import EthernetManager
from property_manager import PropertyManager
from logging import getLogger, StreamHandler, INFO, Formatter, DEBUG
import time
from btn_drv import ButtonDriver, POWER, SW2, SW3, SW4
from view_manager_power import ViewManagerPower
from view_manager import ViewManagerAnalog
from view_manager_info import ViewManagerInfo
from enum import Enum
import os
from threading import Event, Thread
import signal
import sys
from configparser import ConfigParser

# ログの設定
handler = StreamHandler()
handler.setLevel(DEBUG)
handler.setFormatter(Formatter(
    "[%(asctime)s] [%(levelname)s] [%(threadName)s] [%(name)s] %(message)s"))
logger = getLogger()
logger.addHandler(handler)
logger.setLevel(INFO)

# config
iniFile = ConfigParser()
iniFile.read('/home/pi/wisun-gateway/config.ini')

# Wi-SUNマネージャ
wm = WisunManagerFactory.createInstance()
# Ethernetマネージャ
em = EthernetManager()
# Propertyマネージャ
pm = PropertyManager()
pm.setWisunManager(wm)
pm.setEthernetManager(em)
# Viewマネージャ
vmi = ViewManagerInfo(iniFile)
vmp = ViewManagerPower(iniFile)
vmp.setPropertyManager(pm)


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


def main():
    global thread
    global connect_state

    signal.signal(signal.SIGTERM, termed)

    bd = ButtonDriver()

    # EthernetベースのEchonet処理開始
    em.start()

    vm = vmi
    pre_state = connect_state

    # 初期リクエストフラグ
    initReq = True

    # 電源投入時にWi-SUN自動接続
    startConnect()

    while True:
        _conState = connect_state
        if bd.isPressed(SW4):
            state = vm.get_display_state()
            vm.set_display_state(not state)

        if _conState == ConnectState.CONNECTED:
                # Wi-SUN manager の初期リクエストフラグ設定
                wm._initReq = True
                _conState = connect_state = ConnectState.INITIALIZING
        if _conState == ConnectState.INITIALIZING:
            vmi.setInfo('初期化中', int(iniFile.get('view', 'font_info')))
            # 初期リクエストでメーカーコードがキャッシュされるのを待つ
            unit = pm._cache.get(0xe1)  # 積算電力量単位（正方向、逆方向計測値）
            mcode = pm._cache.get(0x8a) # メーカーコード
            if unit is not None and mcode is not None:
                if len(mcode.EDT):
                    # echonet_lite/__init__.py の Node _mcode プロパティへ設定
                    em._node._mcode = mcode.EDT
                if len(unit.EDT): # 積算電力量単位は必須
                    wm._initReq = False
                    _conState = connect_state = ConnectState.ACQUIRING
        if _conState == ConnectState.ACQUIRING:
            vmi.setInfo('取得中', int(iniFile.get('view', 'font_info')))
            if pm._cache.get(0xe7) is not None:
                _conState = connect_state = ConnectState.READY

        if _conState == ConnectState.READY:
            if bd.isPressed(SW3):
                # スマートメータ切断
                if wm is not None:
                    wm.disconnect()
                    _conState = connect_state = ConnectState.DISCONNECT
        elif _conState == ConnectState.DISCONNECT:
            vmi.setInfo('未接続', int(iniFile.get('view', 'font_info')))
            if bd.isPressed(SW2) and thread is None:
                startConnect()
        elif _conState == ConnectState.CONNECTING:
            vmi.setInfo('接続中', int(iniFile.get('view', 'font_info')))
        elif _conState == ConnectState.CONNECT_ERROR:
            vmi.setInfo('接続失敗', int(iniFile.get('view', 'font_info')))
            if bd.isPressed(SW2) and thread is None:
                startConnect()
        elif _conState == ConnectState.DEVICE_ERROR:
            vmi.setInfo('無線モジュール異常', int(iniFile.get('view', 'font_small')))
        if _conState == ConnectState.READY:
            vm = vmp
        else:
            vm = vmi
        if pre_state != _conState:
            vm.clearPayload()
            if _conState == ConnectState.READY:
                vm.set_display_state(False)
        vm.reflesh()
        pre_state = connect_state

        if bd.isLongPressed(POWER):
            logger.info("pressed")
            vm.set_display_state(True)
            vmi.setInfo('シャットダウン中', int(iniFile.get('view', 'font_small')))
            vm = vmi
            vm.clearPayload()
            vm.reflesh()
            # 終了処理
            bd.enablePowerButton()
            dispose()
            # シャットダウンコマンド
            os.system("sudo shutdown -h now")
            return
        time.sleep(0.1)

# Wi-SUN接続タスク起動


def startConnect():
    if wm is None:
        return
    global thread
    global connect_state
    connect_state = ConnectState.CONNECTING
    thread = Thread(target=connect_task)
    thread.start()

# Wi-SUN接続タスク


def connect_task():
    global thread
    global connect_state
    # スマートメータ接続
    logger.info('接続開始')
    connected = wm.connect()
    if connected:
        logger.info('接続成功')
        connect_state = ConnectState.CONNECTED
    else:
        logger.info('接続失敗')
        connect_state = ConnectState.CONNECT_ERROR
    thread = None


def dispose():
    # EthernetベースのEchonet処理終了
    em.stop()
    # スマートメータ切断
    if wm is not None:
        wm.disconnect()
        wm.dispose()


def termed(signum, frame):
    logger.info('SIGTERM!')
    dispose()
    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt')
        dispose()
