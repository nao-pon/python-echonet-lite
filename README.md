# Wi-SUN Gateway

## 概要

Ｂルート接続されたスマートメータとの Wi-SUN 通信を、 Ethernet 通信に変換するものです。

## 変更点

- 本プロダクトは、Keisuke Minami 氏の[python-echonet-lite](https://github.com/kminami/python-echonet-lite)を流用しています。
- 変更点は以下の通りです。
  - Frame クラス
    - get_key()メソッドの追加
  - Node クラス
    - socketオブジェクトをローカル変数からインスタンス変数に変更
    - _deliver()メソッドとservice()メソッドの引数に通信相手のIPアドレスを追加
    - sendto()メソッドの追加
  - Property クラス
    - EDT値の取り出し位置を修正
    - Nodeオブジェクトの保持とgetter／setterの追加

## 設定
- config.ini
    - pwd…Bルートパスワード
    - bid…BルートID
    - serial_port…Wi-SUNモジュールが接続されているシリアルデバイス名
    ```
    [smartmeter]
    pwd = <password for B-route>
    bid = <id for B-route>
    serial_port = /dev/ttyAMA0
    ```

## License

Copyright 2014 Keisuke Minami
Copyright 2019 katsumin

Apache License 2.0

[echonet lite]: http://www.echonet.gr.jp/ "ECHONET Lite"
[kadecot]: http://kadecot.net/ "Kadecot"
