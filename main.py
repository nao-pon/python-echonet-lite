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

# ログの設定
handler = StreamHandler()
handler.setLevel(DEBUG)
handler.setFormatter(Formatter(
    "[%(asctime)s] [%(levelname)s] [%(threadName)s] [%(name)s] %(message)s"))
logger = getLogger()
logger.addHandler(handler)
logger.setLevel(INFO)

# Wi-SUNマネージャ
wm = WisunManagerFactory.createInstance()
# Ethernetマネージャ
em = EthernetManager()
# Propertyマネージャ
pm = PropertyManager()
pm.setWisunManager(wm)
pm.setEthernetManager(em)
# Viewマネージャ
vmi = ViewManagerInfo()
vmp = ViewManagerPower()
vmp.setPropertyManager(pm)


class ConnectState(Enum):
    DISCONNECT = 0
    CONNECTING = 1
    CONNECTED = 2
    CONNECT_ERROR = 3
    DEVICE_ERROR = 4


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
    while True:
        if connect_state == ConnectState.CONNECTED:
            if bd.isPressed(SW3):
                # スマートメータ切断
                if wm is not None:
                    wm.disconnect()
        elif connect_state == ConnectState.DISCONNECT:
            vmi.setInfo('未接続', 20)
            if bd.isPressed(SW2) and thread is None:
                startConnect()
        elif connect_state == ConnectState.CONNECTING:
            vmi.setInfo('接続中', 20)
        elif connect_state == ConnectState.CONNECT_ERROR:
            vmi.setInfo('接続失敗', 20)
            if bd.isPressed(SW2) and thread is None:
                startConnect()
        elif connect_state == ConnectState.DEVICE_ERROR:
            vmi.setInfo('無線モジュール異常', 10)
        if pre_state != connect_state:
            if connect_state == ConnectState.CONNECTED:
                vm = vmp
            else:
                vm = vmi
            vm.clearPayload()
        vm.reflesh()
        pre_state = connect_state

        if bd.isLongPressed(POWER):
            logger.info("pressed")
            vmi.setInfo('シャットダウン中', 12)
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
