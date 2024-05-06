# coding: utf-8
from flask import Flask, render_template, request
from configparser import ConfigParser
import subprocess
import glob

# 初期化
app = Flask(__name__)
INI_FILE = "/home/debian/dg-wisun/config.ini"


# ルートアクセス時の処理
@app.route("/")
def index():
    devices = glob.glob("/dev/ttyS*")
    iniFile = ConfigParser()
    iniFile.read(INI_FILE)
    ini = {
        "pwd": iniFile.get("smartmeter", "pwd"),
        "bid": iniFile.get("smartmeter", "bid"),
        "dev": iniFile.get("smartmeter", "serial_port"),
    }
    return render_template("index.html", devices=devices, ini=ini)


@app.route("/register", methods=["POST"])
def register():
    res = ""
    if request.method == "POST":
        pwd = request.form["pwd"]
        bid = request.form["bid"]
        ser = request.form["ser"]
        iniFile = ConfigParser()
        iniFile.read(INI_FILE)
        iniFile.set("smartmeter", "pwd", pwd)
        iniFile.set("smartmeter", "bid", bid)
        iniFile.set("smartmeter", "serial_port", ser)
        with open(INI_FILE, "w") as fp:
            iniFile.write(fp)
        # wisun-gateway/main.py再起動
        os.system("sudo systemctl restart dgwisun.service")
        res = "config.ini を更新しました"
    return res


@app.route("/restart", methods=["GET"])
def restart():
    # wisun-gateway/main.py再起動
    subprocess.run(["sudo", "systemctl", "restart", "dgwisun.service"])
    res = "dgwisun.service をリスタートしました"
    return res


@app.route("/reboot", methods=["GET"])
def reboot():
    # wisun-gateway/main.py再起動
    subprocess.run(["sudo", "systemctl", "reboot"])
    res = "DG Wi-SUN ブリッジをリブートしました"
    return res


if __name__ == "__main__":
    print("start")
    app.run()
