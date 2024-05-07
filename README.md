# Wi-SUN Gateway for Home Assistant

## 概要

Ｂルート接続されたスマートメータとの Wi-SUN 通信を、 Ethernet または WiFi 通信に変換するものです。

このリポジトリのバージョンは、Home Assistant のカスタムコンポーネント [echonetlite_homeassistant](https://github.com/scottyphillips/echonetlite_homeassistant) で動作するように調整が加えられています。

また、この dg-wisun ブランチは、秋月電子で販売されている「[部品取りに!無線モジュール付きSoc基板+白色プラスチックケース](https://akizukidenshi.com/catalog/g/g117437/)」で動作するように変更が加えられています。
インストールに記載されている手順をもとに Debian GNU/Linux が動作するようにセットアップを行ってください。

## 変更点

- 本プロダクトは、katsumin 氏の[python-echonet-lite](https://github.com/katsumin/python-echonet-lite)から派生しています。
- 変更点は以下の通りです。
    - 起動時に自動接続するようになっています。
    - 右側青色LED3灯が点灯
    - 接続完了後に、必須プロパティ(メーカーコード、積算電力量単位)の取得を行います。
    - 右側青色LEDは
        - 接続開始時に3灯点灯
        - Wi-SUNモジュール接続完了時に2灯点灯
        - 初期キャッシュ完了時に1灯点灯
        - 準備完了で消灯となります。
    - Home Assistant でセットアップする場合は、青色LEDが消えてからセットアップをするとスムーズです。
    - 緑色LEDは電源、その隣の青色LEDは送受信時に点滅します。

## インストール

- Debian 化の成功事例[秋月のSoC基板 (白い箱) にDebianを入れる](https://qiita.com/chibiegg/items/4b1b70a5ba09c4a52a12) に沿って Debian を稼働できる状態にします。

- 【ソース取得】
    - SSH で接続し debian でログインしてソースを取得します。
    ```
    sudo apt update
    sudo apt upgrade
    sudo apt -y install git
    git clone -b dg-wisun https://github.com/nao-pon/python-echonet-lite dg-wisun
    ```
- 【sudo コマンドのパスワードなし設定】
    - apt, cp, systemctl, pip3 コマンドを sudo でパスワードなしで実行できるように設定します。
    ```
    cd dg-wisun
    sudo cp ./dgwisun.sudoers /etc/sudoers.d/dgwisun
    sudo chmod 0440 /etc/sudoers.d/dgwisun
    ```

- 【インストール】
    - 依存ライブラリ取得
    - 関連ツールのインストール
    - 自動起動設定
    ```
    sh install.sh
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
        serial_port = /dev/ttyS1
        ```
    1. ブラウザで「http://<IP アドレス>:9000」にアクセスして、Ｂルートパスワード・ＢルートＩＤ・シリアルデバイス名を設定する。

        ![](web-config.png)

## Home Assistant

Home Assistant において、ECHONET Lite 統合を通して利用できます。

ECHONET Lite 統合をインストールして、「設定」-「統合」-「統合を追加」で ECHONET Lite を選択します。

![Wi-SUN-Ethernet-1](https://user-images.githubusercontent.com/1412630/199409452-7129f9a6-0f84-4de0-a04e-d3354e1d1796.png)

このプロダクトが正常に機能していると、「送信(Submit)」をクリックして少し待つと、自動的に検出されます。

![Wi-SUN-Ethernet-2](https://user-images.githubusercontent.com/1412630/199409820-524072a1-f7b7-4c7c-a843-b7d35936ec91.png)

更に進めると、Low voltage smart electric energy meter のデバイスが認識されます。

![Wi-SUN-Ethernet-3](https://user-images.githubusercontent.com/1412630/199410408-d381ee93-144a-40fa-ab95-6e4f9ddb8684.png)
![Wi-SUN-Ethernet-4](https://user-images.githubusercontent.com/1412630/199410487-aeed3935-ab6d-43cc-b712-09f0a1659dcc.png)

これで以下のように Home Assistant 上でデバイスを利用できるようになります。

![Wi-SUN-Ethernet-5](https://user-images.githubusercontent.com/1412630/199410657-d089d043-df94-43f4-9732-7bd3680988e7.png)
![Wi-SUN-Ethernet-6](https://user-images.githubusercontent.com/1412630/199410673-fd0b4c96-1f78-4d92-bed3-e56f1ae5ba9e.png)

## License

Copyright 2014 Keisuke Minami

Copyright 2019 katsumin

Copyright 2022-2024 Naoki Sawada

Apache License 2.0

[echonet lite: https://echonet.jp/](https://echonet.jp/) "ECHONET Lite"

[kadecot: https://kadecot.net/](https://web.archive.org/web/20170607015901/https://kadecot.net/) "Kadecot"

