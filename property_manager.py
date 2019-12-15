# coding: utf-8
from echonet_lite import Frame, Property
import datetime
import time
import subprocess
import struct
from logging import getLogger, StreamHandler, INFO, Formatter
logger = getLogger(__name__)


class PropertyManager:
    # キャッシュ対象のEPC
    cacheEPCs = (0x82, 0x8a, 0x8d, 0x9d, 0x9e, 0x9f, 0xe7, 0xe8)
    # サポートするEPC
    supportEPCs = [0x80, 0x81, 0x82, 0x88, 0x8a, 0x8d, 0x97, 0x98, 0x9d, 0x9e, 0x9f,
                   0xd3, 0xd7, 0xe0, 0xe1, 0xe2, 0xe3, 0xe4, 0xe5, 0xe7, 0xe8, 0xea, 0xeb, 0xec, 0xed]
    # 応答ESV
    resESVs = [0x72, 0x7a, 0x7e]
    # 通知ESV
    infESVs = [0x73, 0x74]

    def __init__(self):
        self._cache = {}
        self._requests = {}

    def setWisunManager(self, wisun):
        self._wisun = wisun
        if wisun is None:
            return
        wisun.setPropertyManager(self)

    def setEthernetManager(self, ether):
        self._ether = ether
        ether.setPropertyManager(self)

    # プロパティ取得（EPC指定）
    def getEPC(self, epc):
        if epc in self._cache:
            return self._cache[epc]
        else:
            return None

    # プロパティ取得
    def get(self, frame):
        # 応答フレーム
        res_frame = Frame.create_response(frame)
        # 不可応答フレーム
        res_er_frame = Frame.create_response(frame)
        res_er_frame.ESV = 0x52
        # 要求フレーム
        req_frame = Frame([frame.EHD1, frame.EHD2, frame.TID,
                           frame.SEOJ, frame.DEOJ, frame.ESV])
        # cached = True
        for prop in frame.properties:
            if prop.EPC in self._cache:
                # キャッシュ済みのEPC
                res_frame.properties.append(self._cache[prop.EPC])
            elif prop.EPC not in PropertyManager.supportEPCs:
                # 未サポートのEPC
                res_er_frame.properties.append(prop)
            else:
                req_frame.properties.append(prop)
                # cached = False
        if len(frame.properties) == len(res_frame.properties):
            # epcListに対するデータが全てキャッシュ済み
            return res_frame
        elif len(res_er_frame.properties) > 0:
            # 不可応答のフレーム
            return res_er_frame
        else:
            # 未キャッシュのEPCがあった → 要求フレームを取っておく
            key = frame.get_key()
            self._requests[key] = frame
            # WisunManagerに要求
            self._wisun.get(req_frame)
            return key

    # プロパティ設定
    def put(self, frame, key):
        # 対象ならキャッシュ
        props = {}
        for p in frame.properties:
            props[p.EPC] = p
            # if p.EPC in PropertyManager.cacheEPCs:
            #     self._cache[p.EPC] = p
            self._cache[p.EPC] = p
        logger.info(
            "PropertyManager.put cache-keys:{0}".format(self._cache.keys()))
        # 要求IDから要求フレーム
        if frame.ESV in PropertyManager.resESVs:
            if key in self._requests:
                req_frame = self._requests[key]
                del self._requests[key]
                # 応答フレーム
                res_frame = Frame.create_response(req_frame)
                for p in req_frame.properties:
                    if p.EPC in self._cache:
                        # キャッシュから
                        res_frame.properties.append(self._cache[p.EPC])
                    else:
                        # スマートメータ応答から
                        res_frame.properties.append(props[p.EPC])
                # Ethernet response
                self._ether.sendResponse(res_frame, key)
        elif frame.ESV in PropertyManager.infESVs:
            self._ether.sendNotification(frame)

    # def recordData(self, properties):
    #     text = ''
    #     for p in properties:
    #         if p.EPC == 0xe7:
    #             d = datetime.datetime.today()
    #             values = struct.unpack('>l', p.EDT)
    #             timestamp = int(time.mktime(d.timetuple())) * 1000000000
    #             text += 'power value={0} {1}\n'.format(values[0], timestamp)
    #         elif p.EPC == 0xea:
    #             values = struct.unpack('>HBBBBBL', p.EDT)
    #             d = time.strptime("{0:04d}/{1:02d}/{2:02d} {3:02d}:{4:02d}:{5:02d}".format(values[0],values[1],values[2],values[3],values[4],values[5]), "%Y/%m/%d %H:%M:%S")
    #             timestamp = int(time.mktime(d)) * 1000000000
    #             text += '+power value={0} {1}\n'.format(values[6], timestamp)
    #         elif p.EPC == 0xeb:
    #             values = struct.unpack('>HBBBBBL', p.EDT)
    #             d = time.strptime("{0:04d}/{1:02d}/{2:02d} {3:02d}:{4:02d}:{5:02d}".format(values[0],values[1],values[2],values[3],values[4],values[5]), "%Y/%m/%d %H:%M:%S")
    #             timestamp = int(time.mktime(d)) * 1000000000
    #             text += '-power value={0} {1}\n'.format(values[6], timestamp)
    #     d = datetime.datetime.today()
    #     f = open('power{0:04d}{1:02d}{2:02d}.txt'.format(d.year,d.month,d.day), 'a')
    #     f.write(text)
    #     f.close()
    #     # subprocess.call("cat ./power_tmp.txt >> power{0:04d}{1:02d}{2:02d}.txt".format(d.year,d.month,d.day))
    #     # subprocess.call('ls power_tmp.txt')
    #     logger.info(text)
