# coding: utf-8
from luma.core import cmdline, error
from luma.core.render import canvas
from PIL import ImageFont
from view_manager import ViewManager
import struct
from property_manager import PropertyManager
from echonet_lite import Frame, Property


class ViewManagerPower(ViewManager):
    """ 電力表示View """

    # 初期化
    def __init__(self, iniFile):
        super().__init__(iniFile)
        self._offset_x = self._payloadArea[0]
        self._offset_y = self._payloadArea[1]
        self._power = 0
        self._current_r = 0
        self._current_t = 0
        self._font_size = int(iniFile.get('view', 'font_middle'))
        self._font_name = iniFile.get('view', 'payload_font')
        self._fontPower = self.make_font(
            self._font_name, int(iniFile.get('view', 'font_power')))

    # ペイロードの表示
    def refleshPayload(self, draw):
        if self._pm is not None:
            prop = self._pm.getEPC(0xe7)
            if prop is not None:
                # print(prop.EDT)
                va = struct.unpack('>l', prop.EDT)
                self._power = va[0]
            prop = self._pm.getEPC(0xe8)
            if prop is not None:
                # print(prop.EDT)
                va = struct.unpack('>hh', prop.EDT)
                self._current_r = va[0] / 10.0
                self._current_t = va[1] / 10.0
        font = self._font
        font_p = self._fontPower
        width = self._payloadArea[2] - self._offset_x
        height = self._payloadArea[3] - self._offset_y
        power_h = (height) / 3
        w, h = draw.textsize('瞬', font=font)
        unit_w, unit_h = draw.textsize('W', font=font)
        x = 2
        # 瞬時電力
        y = height / 2 + power_h * (-1) - h / 2 + self._offset_y
        draw.text((x, y), '瞬時電力:', fill="green", font=font)
        draw.text((width - unit_w, y), 'W', fill="green", font=font)
        s = '{0:5d}'.format(self._power)
        value_w, value_h = draw.textsize(s, font=font_p)
        draw.text((width - unit_w - value_w - 1, y + h - value_h),
                  s, fill="yellow", font=font_p)
        # 電流R相
        y = height / 2 + power_h * (0) - h / 2 + self._offset_y
        draw.text((x, y), '電流Ｒ相:', fill="green", font=font)
        draw.text((width - unit_w, y), 'A', fill="green", font=font)
        s = '{0:5.1f}'.format(self._current_r)
        value_w, value_h = draw.textsize(s, font=font_p)
        draw.text((width - unit_w - value_w - 1, y + h - value_h),
                  s, fill="yellow", font=font_p)
        # 電流T相
        y = height / 2 + power_h * (1) - h / 2 + self._offset_y
        draw.text((x, y), '電流Ｔ相:', fill="green", font=font)
        draw.text((width - unit_w, y), 'A', fill="green", font=font)
        s = '{0:5.1f}'.format(self._current_t)
        value_w, value_h = draw.textsize(s, font=font_p)
        draw.text((width - unit_w - value_w - 1, y + h - value_h),
                  s, fill="yellow", font=font_p)
