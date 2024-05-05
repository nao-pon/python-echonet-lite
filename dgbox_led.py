class DGboxLed:
    def __init__(self):
        self.clear()

    def __led(self, nLedNumber, nLedCmd):
        if (nLedNumber >= 1) and (nLedNumber <= 4):
            szDir = "/sys/class/leds/led{0:1d}/brightness".format(nLedNumber)
            if nLedCmd == 0:
                szCmd = "0"
            else:
                szCmd = "1"
            fDev = open(szDir, "w")
            fDev.write(szCmd)
            fDev.close()

    def clear(self):
        nLedNumber = 4
        while nLedNumber > 0:
            self.__led(nLedNumber, 0)
            nLedNumber -= 1

    # Aki-boxのLEDを点灯する(nLedNumberは 1～4)
    def on(self, nLedNumber):
        self.__led(nLedNumber, 1)

    # Aki-boxのLEDを消灯する(nLedNumberは 1～4)
    def off(self, nLedNumber):
        self.__led(nLedNumber, 0)
