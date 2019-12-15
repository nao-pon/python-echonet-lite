# coding: utf-8
from gpiozero import Button, LED, InputDevice

POWER = 0
SW2 = 1
SW3 = 2
SW4 = 3

# pin, pullup, active_state, bounce_time, hold_time
gpio_pins = [
    [5, True, None, None, 2],
    [9, True, None, None, 2],
    [22, True, None, None, 2],
    [23, True, None, None, 2]
]


class ButtonDriver:
    """
    ボタン・ドライバ
    """

    # 初期化
    def __init__(self):
        self._pre = []
        self._sw = []
        self.disablePowerButton()
        for i in range(len(gpio_pins)):
            self._sw.append(
                Button(gpio_pins[i][0], gpio_pins[i][1], gpio_pins[i][2], gpio_pins[i][3], gpio_pins[i][4], False))
            self._pre.append(False)
        return

    # 押下チェック
    #  index
    def isPressed(self, index):
        _cur = self._sw[index].is_pressed
        s = not self._pre[index] and _cur
        self._pre[index] = _cur
        return s

    # 長押しチェック
    #  index
    def isLongPressed(self, index):
        return self._sw[index].is_held

    # 電源ONボタンの無効化
    def disablePowerButton(self):
        self._ponDis = LED(4)

    # 電源ONボタンの有効化
    def enablePowerButton(self):
        # self._ponDis.on()
        self._ponDis.close()
        LED(4,False)
        # self._sw[POWER].close()
        # LED(gpio_pins[POWER][0],False)
        # self._ponDis.close()
        # InputDevice(4,True)
        # InputDevice(23,True)
#        b = Button(4,False,True)
#        b.close()
