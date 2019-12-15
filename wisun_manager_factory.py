import serial
from configparser import ConfigParser
import bp35c0
import bp35c0_j11
import logging
logger = logging.getLogger(__name__)

class WisunManagerFactory:
    # Wi-SUNマネージャ・インスタンス化
    @staticmethod
    def createInstance():
        # config読み込み
        iniFile = ConfigParser()
        iniFile.read('/home/pi/wisun-gateway/config.ini')
        pwd = iniFile.get('smartmeter', 'pwd')
        bid = iniFile.get('smartmeter', 'bid')
        dev = iniFile.get('smartmeter', 'serial_port')
        # BP35C0を試す
        logger.info('try BP35C0..')
        wm = bp35c0.WisunManager(pwd,bid,dev)
        if wm.isActive():
            return wm
        wm.dispose()
        # BP35C0-J11を試す
        logger.info('try BP35C0-J11..')
        wm = bp35c0_j11.WisunManager(pwd,bid,dev)
        if wm.isActive():
            return wm
        wm.dispose()
        return None
