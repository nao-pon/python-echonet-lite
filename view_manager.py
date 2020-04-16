# coding: utf-8
from abc import ABCMeta, abstractmethod
import sys
import math
import os
import datetime
import time
from luma.core import cmdline, error
from luma.core.render import canvas
from PIL import ImageFont
import netifaces
from property_manager import PropertyManager


class ViewManager(metaclass=ABCMeta):
    "Viewマネージャ"

    # 初期化
    def __init__(self, iniFile):
        self._device = self.get_device(
            ['--config', iniFile.get('view', 'config_file')])
        self._width = min(self._device.width, 240)
        self._height = min(self._device.height, 240)
        self._font = self.make_font(iniFile.get(
            'view', 'header_font'), int(iniFile.get('view', 'font_small')))
        self._date = None
        self._pm = None
        with canvas(self._device) as draw:
            text_w, text_h = draw.textsize('t', self._font)
            self._payloadArea = (0, text_h, self._width -
                                 1, self._height - 1 - text_h)

    # Propertyマネージャ設定
    def setPropertyManager(self, pm):
        self._pm = pm

    # フォント生成
    def make_font(self, name, size):
        font_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 'fonts', name))
        return ImageFont.truetype(font_path, size)

    # 表示更新
    def reflesh(self):
        with canvas(self._device) as draw:
            # 外枠
            # draw.rectangle((0, 0, self._width - 1, self._height - 1), outline="blue")
            # draw.rectangle((self._payloadArea[0],self._payloadArea[1]-1,self._payloadArea[2],self._payloadArea[3]+1), outline="blue")
            draw.line((self._payloadArea[0], self._payloadArea[1]-1,
                       self._payloadArea[2], self._payloadArea[1]-1), fill="blue")
            draw.line((self._payloadArea[0], self._payloadArea[3]+1,
                       self._payloadArea[2], self._payloadArea[3]+1), fill="blue")

            # 日付
            now = datetime.datetime.now()
            self._date = now
            dt = u"'{0:02}/{1:02}/{2:02} {3:02}:{4:02}:{5:02}".format(
                now.year % 100, now.month, now.day, now.hour, now.minute, now.second)
            # date_w, date_h = draw.textsize("'88/88/88 88:88:88", self._font)
            date_w, date_h = draw.textsize(dt, self._font)
            draw.text(((self._width - date_w)/2, self._height -
                       date_h), dt, fill="yellow", font=self._font)
            # IP Address更新
            self.refleshIpAddr(draw)
            # ペイロード更新
            self.refleshPayload(draw)

    # IPアドレスの表示
    def refleshIpAddr(self, draw):
        addr = None
        try:
            addr = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']
        except Exception:
            try:
                addr = netifaces.ifaddresses(
                    'wlan0')[netifaces.AF_INET][0]['addr']
            except Exception:
                pass
        if addr is not None:
            addr_w, addr_h = draw.textsize(addr, self._font)
            draw.text(((self._width - addr_w)/2, 0), addr,
                      fill="yellow", font=self._font)

    # ペイロード表示のクリア
    def clearPayload(self):
        with canvas(self._device) as draw:
            draw.rectangle((self._payloadArea[0], self._payloadArea[1],
                            self._payloadArea[2], self._payloadArea[3]), fill="black", outline="black")

    @abstractmethod
    # ペイロードの表示
    def refleshPayload(self, draw):
        pass

    # 表示デバイス取得
    def get_device(self, actual_args):
        # if actual_args is None:
        #     actual_args = sys.argv[1:]
        # print(actual_args)
        parser = cmdline.create_parser(description='luma.examples arguments')
        args = parser.parse_args(actual_args)

        if args.config:
            # load config from file
            config = cmdline.load_config(args.config)
            args = parser.parse_args(config + actual_args)

        # create device
        try:
            device = cmdline.create_device(args)
        except error.Error as e:
            parser.error(e)

        return device

    def dispose(self):
        pass


class ViewManagerAnalog(ViewManager):
    def __init__(self):
        super().__init__()
        self._offset_x = self._payloadArea[0]
        self._offset_y = self._payloadArea[1]
        width = self._payloadArea[2] - self._offset_x
        height = self._payloadArea[3] - self._offset_y
        self._cy = height / 2 + self._offset_y
        self._radius = (min(width, height) - 1) / 2
        self._cx = width / 2

    def posn(self, angle, arm_length):
        dx = int(math.cos(math.radians(angle)) * arm_length)
        dy = int(math.sin(math.radians(angle)) * arm_length)
        return (dx, dy)

    def refleshPayload(self, draw):
        if self._date is not None:
            cx = self._cx
            cy = self._cy
            radius = self._radius
            # calc. angles
            now = self._date
            hrs_angle = 270 + (30 * (now.hour + (now.minute / 60.0)))
            # hrs = posn(hrs_angle, cy - margin - 7)
            hrs = self.posn(hrs_angle, radius - 7)
            min_angle = 270 + (6 * now.minute)
            # mins = posn(min_angle, cy - margin - 2)
            mins = self.posn(min_angle, radius - 2)
            sec_angle = 270 + (6 * now.second)
            # secs = posn(sec_angle, cy - margin - 2)
            secs = self.posn(sec_angle, radius - 2)
            # reflet view
            draw.ellipse((cx - radius, cy - radius, cx +
                          radius, cy + radius), outline="white")
            draw.line((cx, cy, cx + hrs[0], cy + hrs[1]), fill="white")
            draw.line((cx, cy, cx + mins[0], cy + mins[1]), fill="white")
            draw.line((cx, cy, cx + secs[0], cy + secs[1]), fill="red")
            draw.ellipse((cx - 2, cy - 2, cx + 2, cy + 2),
                         fill="white", outline="white")


if __name__ == "__main__":
    vm = ViewManagerAnalog()
    try:
        while True:
            vm.reflesh()
            time.sleep(0.1)
    except KeyboardInterrupt:
        vm.dispose()
