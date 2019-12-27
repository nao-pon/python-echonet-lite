sudo apt -y install python-dev python-pip python3-pip libfreetype6-dev libjpeg-dev build-essential libopenjp2-7 libtiff5 nginx uwsgi-plugin-python3
pip3 install luma.core luma.oled luma.lcd netifaces gpiozero
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
sudo cp ./sample.service /etc/systemd/system
sudo systemctl enable uwsgi.service
sudo systemctl restart nginx
sudo systemctl restart uwsgi.service
sudo systemctl enable sample.service
sudo systemctl start sample.service
