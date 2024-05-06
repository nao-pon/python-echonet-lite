sudo apt -y install python3 python3-pip nginx uwsgi-plugin-python3
sudo pip3 install pyserial
sudo -H pip3 install flask
ls ./nginx/log >/dev/null 2>&1
if [ $? -ne 0 ]; then
    mkdir ./nginx/log
fi
ls ./nginx/tmp >/dev/null 2>&1
if [ $? -ne 0 ]; then
    mkdir ./nginx/tmp
fi
sudo cp ./nginx/default.conf /etc/nginx/conf.d/default.conf
sudo cp ./nginx/uwsgi.service /etc/systemd/system
sudo cp ./dgwisun.service /etc/systemd/system
cp ./config.ini.default ./config.ini
sudo systemctl enable uwsgi.service
sudo systemctl restart nginx
sudo systemctl restart uwsgi.service
sudo systemctl enable dgwisun.service
sudo systemctl start dgwisun.service
