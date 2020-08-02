from echonet_lite import Frame, Property
import datetime
import time
import subprocess
import struct
from configparser import ConfigParser, NoOptionError, NoSectionError
from influxdb import InfluxDBClient
from logging import getLogger, StreamHandler, INFO, Formatter
logger = getLogger(__name__)


class InfluxManager:
    def __init__(self):
        # 積算電力係数
        self._k = 0.1
        # config読み込み
        iniFile = ConfigParser()
        iniFile.read('/home/pi/wisun-gateway/config.ini')
        try:
            url = iniFile.get('influxdb', 'url')
            self._client = InfluxDBClient(
                url, 8086, 'root', 'root', 'smartmeter')
        except (NoSectionError, NoOptionError):
            self._client = None

    def put(self, properties):
        text = ''
        for p in properties:
            if p.EPC == 0xe7:
                d = datetime.datetime.today()
                values = struct.unpack('>l', p.EDT)
                timestamp = int(time.mktime(d.timetuple())) * 1000000000
                text += 'power value={0} {1}\n'.format(values[0], timestamp)
            elif p.EPC == 0xea:
                values = struct.unpack('>HBBBBBL', p.EDT)
                d = time.strptime("{0:04d}/{1:02d}/{2:02d} {3:02d}:{4:02d}:{5:02d}".format(
                    values[0], values[1], values[2], values[3], values[4], values[5]), "%Y/%m/%d %H:%M:%S")
                timestamp = int(time.mktime(d)) * 1000000000
                text += '+power value={0} {1}\n'.format(
                    values[6] * 0.1, timestamp)
            elif p.EPC == 0xeb:
                values = struct.unpack('>HBBBBBL', p.EDT)
                d = time.strptime("{0:04d}/{1:02d}/{2:02d} {3:02d}:{4:02d}:{5:02d}".format(
                    values[0], values[1], values[2], values[3], values[4], values[5]), "%Y/%m/%d %H:%M:%S")
                timestamp = int(time.mktime(d)) * 1000000000
                text += '-power value={0} {1}\n'.format(
                    values[6] * 0.1, timestamp)
        d = datetime.datetime.today()
        f = open(
            '/home/pi/wisun-gateway/power{0:04d}{1:02d}{2:02d}.txt'.format(d.year, d.month, d.day), 'a')
        f.write(text)
        f.close()
        if self._client is not None:
            try:
                self._client.write_points(text, protocol='line')
            except Exception:
                pass
        logger.info(text)
