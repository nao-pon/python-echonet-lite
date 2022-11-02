# coding: utf-8
import time
from echonet_lite import Object, Frame, Property
from logging import getLogger, StreamHandler, INFO, Formatter
logger = getLogger(__name__)
logger.setLevel(INFO)

DISPLAY_ON = 0x30.to_bytes(1, 'big')
DISPLAY_OFF = 0x31.to_bytes(1, 'big')

class DisplayManager(Object):
    ''' General Lighting Object (group=0x02, class=0x90) '''

    def __init__(self):
        Object.__init__(self, 0x06, 0x01)
        self._vm = None
        self._em = None

    # Viewマネージャ設定
    def setViewManager(self, vm):
        self._vm = vm
        vm.setDisplayManager(self)

    # Ethernetマネージャ設定
    def setEthernetManager(self, em):
        self._em = em

    def service(self, frame, addr):
        if self._vm is None:
            return None

        logger.info(frame)

        if frame.ESV == 0x61:  # SetC
            new_frame = Frame.create_response(frame)
            for prop in frame.properties:
                if prop.EPC == 0x80:  # power (0x30=ON, 0x31=OFF)
                    if prop.EDT == DISPLAY_ON:
                        self._vm.set_display_state(True)
                    else:
                        self._vm.set_display_state(False)
                    prop.EDT = b'' # Set 成功時は EDT を返さない
                    new_frame.properties.append(prop)
            return new_frame
        elif frame.ESV == 0x62: # Get
            new_frame = Frame.create_response(frame)
            for prop in frame.properties:
                if prop.EPC == 0x80:  # power (0x30=ON, 0x31=OFF)
                    if self._vm.get_display_state():
                        prop.EDT = DISPLAY_ON
                    else:
                        prop.EDT = DISPLAY_OFF
                    new_frame.properties.append(prop)
                elif prop.EPC in (0x9D, 0x9E, 0x9F): # stat/set/get map
                    prop.EDT = b'\x01\x80'
                    new_frame.properties.append(prop)
            return new_frame

    def notify(self, state):
        if state:
            edt = 0x30
        else:
            edt = 0x31
        frame = Frame(bytearray([
                    0x10, 0x81, 0x00, 0x00, # Header
                    0x06, 0x01, 0x01,       # SEOJ
                    0x05, 0xff, 0x01,       # DEOJ
                    0x73,                   # ESV (Notify)
                    0x01,                   # OPC
                    0x80, 0x01, edt         # EPC, PDC, EDT
                ]))

        self._em.sendNotification(frame)
