# coding: utf-8
from flask import Flask, render_template, request
from configparser import ConfigParser
import os
import glob

# 初期化
app = Flask(__name__)
INI_FILE = '/home/pi/wisun-gateway/config.ini'

# ルートアクセス時の処理
@app.route('/')
def index():
    devices = glob.glob('/dev/tty[A-Za-z]*')
    return render_template('index.html', devices=devices)


@app.route('/register', methods=['POST'])
def register():
    res = ""
    if request.method == 'POST':
        pwd = request.form['pwd']
        bid = request.form['bid']
        ser = request.form['ser']
        iniFile = ConfigParser()
        iniFile.read(INI_FILE)
        iniFile.set('smartmeter', 'pwd', pwd)
        iniFile.set('smartmeter', 'bid', bid)
        iniFile.set('smartmeter', 'serial_port', ser)
        with open(INI_FILE, 'w') as fp:
            iniFile.write(fp)
        # wisun-gateway/main.py再起動
        os.system('sudo systemctl restart sample.service')
        res = "config.ini を更新しました"
    return res


@app.route('/restart', methods=['GET'])
def restart():
    # wisun-gateway/main.py再起動
    os.system('sudo systemctl restart sample.service')
    res = "sample.service をリスタートしました"
    return res


if __name__ == "__main__":
    print('start')
    app.run()
