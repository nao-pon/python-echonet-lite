from property_manager import PropertyManager 
from view_manager import ViewManager

class ViewManagerInfo(ViewManager):
    """ 情報表示View """

    # 初期化
    def __init__(self):
        super().__init__()
        self._offset_x = self._payloadArea[0]
        self._offset_y = self._payloadArea[1]
        self._info = None
        self._font_size = 20
        # self._font_name = "UnDotum.ttf"
        self._font_name = "code2000.ttf"
        self._fontInfo = self.make_font(self._font_name, self._font_size)

    # 出力情報設定
    def setInfo(self, info, font_size):
        self._info = info
        if self._font_size != font_size:
            self._font_size = font_size
            self._fontInfo = self.make_font(self._font_name, self._font_size)

    # ペイロードの表示
    def refleshPayload(self, draw):
        if self._info is not None:
            font = self._fontInfo
            width = self._payloadArea[2] - self._offset_x
            height = self._payloadArea[3] - self._offset_y
            w,h = draw.textsize(self._info, font=font)
            x = (width - w) / 2 + self._offset_x
            y = (height - h) / 2 + self._offset_y 
            draw.text((x, y), self._info, fill="green", font=font)


