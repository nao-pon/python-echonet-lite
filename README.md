# Wi-SUN Gateway for Home Assistant

## 概要

Ｂルート接続されたスマートメータとの Wi-SUN 通信を、 Ethernet または WiFi 通信に変換するものです。

このリポジトリのバージョンは、Home Assistant のカスタムコンポーネント [echonetlite_homeassistant](https://github.com/scottyphillips/echonetlite_homeassistant) で動作するように調整が加えられています。

## 変更点

- 本プロダクトは、katsumin 氏の[python-echonet-lite](https://github.com/katsumin/python-echonet-lite)から派生しています。
- 変更点は以下の通りです。
    - 起動時に自動接続するようになっています。
    - 接続完了後に、必須プロパティ(メーカーコード、積算電力量単位)の取得を行います。
    - その後、データが取得できたら画面をOFFにします。
    - 画面OFF時は、バックライトも消灯します。
    - Home Assistant でセットアップする場合は、画面が消えてからセットアップをするとスムーズです。

## インストール

- Raspberry Pi OS Lite (32bit) 動作確認は Raspberry Pi Zero WH 上で実行
    - 動作確認時のバージョン -> [September 22nd 2022](https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2022-09-26/2022-09-22-raspios-bullseye-armhf-lite.img.xz)
    - SDカードの Boot パーティションの設定
        - ssh の有効化
            - ファイル名 `ssh` で空ファイルを作成
        - WiFi 設定
            - ファイル名 `wpa_supplicant.conf` を作成
                ```
                ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
                update_config=1
                country=JP

                network={
                 ssid="あなたのSSID"
                 psk="あなたのパスワード"
                }
                ```
        - pi ユーザーの作成
            - パスワードハッシュの作成
                - 手持ちの Linux シェルで以下を実行 (-6 は -5, -1, なし も可)
                    ```
                    openssl passwd -6 設定するパスワード
                    ```
            - ファイル名 `userconf` を作成
                ```
                pi:作成したパスワードハッシュ
                ```

-   環境設定 (ネットワーク越しにSSHログインできる)
    ```
    pi@raspberrypi:~ $ sudo raspi-config
    ```
    - 3 Interface Options (SPI, ハードウェアシリアルを有効にする)
        - I4 SPI
            - Would you like the SPI interface to be enabled? -> Yes
        - I6 Serial Port
            - Would you like a login shell to be accessible over serial? -> No
            - Would you like the serial port hardware to be enabled? -> Yes
    - 5 Localisation Options (タイムゾーンをTokyoにする)
        - L2 Timezone

-   ソース取得

    ```
    pi@raspberrypi:~ $ sudo apt update
    pi@raspberrypi:~ $ sudo apt upgrade
    pi@raspberrypi:~ $ sudo apt -y install git
    pi@raspberrypi:~ $ git clone -b wisun-gateway https://github.com/nao-pon/python-echonet-lite wisun-gateway
    ```

-   インストール
    -   依存ライブラリ取得
    -   関連ツールのインストール
    -   自動起動設定
    ```
    pi@raspberrypi:~ $ cd wisun-gateway
    pi@raspberrypi:~/wisun-gateway $ sh install.sh
    ```

## 設定

-   下記のいずれかの方法で設定する
    1. config.ini を直接編集
        - pwd…Ｂルートパスワード
        - bid…ＢルートＩＤ (ハイフンは含めない)
        - serial_port…Wi-SUN モジュールが接続されているシリアルデバイス名


        ```
        [smartmeter]
        pwd = <password for B-route>
        bid = <id for B-route>
        serial_port = /dev/ttyAMA0
        ```
    1. ブラウザで「http://<IP アドレス>:9000」にアクセスして、Ｂルートパスワード・ＢルートＩＤ・シリアルデバイス名を設定する。

        ![](web-config.png)

- ST7789 ディスプレイを使用時は config.ini の SSD1331 パートをコメントアウトして、ST7789 パートのコメントアウトを外す。

## ハードウェア

Wi-SUN モジュールと Raspberry-pi を接続するアダプターは、スイッチサイエンスで購入可能ですが、在庫はあまりないようです。

- [Wi-SUNゲートウェイキット（RpiWi-001）](https://www.switch-science.com/collections/all/products/6160)
- [Wi-SUNゲートウェイキット（最小コスト版、OLEDタイプ）](https://www.switch-science.com/collections/all/products/6467)
- [Wi-SUNゲートウェイキット（最小コスト版、LCDタイプ）](https://www.switch-science.com/collections/all/products/6466)


下記の回路図を参考に自作することも可能だと思います。

## 回路図

![](schematic.png)


## Home Assistant

Home Assistant において、ECHONET Lite 統合を通して利用できます。

ECHONET Lite 統合をインストールして、「設定」-「統合」-「統合を追加」で ECHONET Lite を選択します。

![Wi-SUN-Ethernet-1](https://user-images.githubusercontent.com/1412630/199409452-7129f9a6-0f84-4de0-a04e-d3354e1d1796.png)

このプロダクトが正常に機能していると、「送信(Submit)」をクリックして少し待つと、自動的に検出されます。

![Wi-SUN-Ethernet-2](https://user-images.githubusercontent.com/1412630/199409820-524072a1-f7b7-4c7c-a843-b7d35936ec91.png)

更に進めると、Low voltage smart electric energy meter と Display の2つのデバイスが認識されます。
Display デバイスは、このプロダクトのディスプレイの On / Off をコントロールできます。

![Wi-SUN-Ethernet-3](https://user-images.githubusercontent.com/1412630/199410408-d381ee93-144a-40fa-ab95-6e4f9ddb8684.png)
![Wi-SUN-Ethernet-4](https://user-images.githubusercontent.com/1412630/199410487-aeed3935-ab6d-43cc-b712-09f0a1659dcc.png)

これで以下のように Home Assistant 上でデバイスを利用できるようになります。

![Wi-SUN-Ethernet-5](https://user-images.githubusercontent.com/1412630/199410657-d089d043-df94-43f4-9732-7bd3680988e7.png)
![Wi-SUN-Ethernet-6](https://user-images.githubusercontent.com/1412630/199410673-fd0b4c96-1f78-4d92-bed3-e56f1ae5ba9e.png)

## License

Copyright 2014 Keisuke Minami

Copyright 2019 katsumin

Copyright 2022 Naoki Sawada

Apache License 2.0

[echonet lite: https://echonet.jp/](https://echonet.jp/) "ECHONET Lite"

[kadecot: https://kadecot.net/](https://web.archive.org/web/20170607015901/https://kadecot.net/) "Kadecot"

