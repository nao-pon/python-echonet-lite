sudo apt -y install python-dev python-pip python3-pip libfreetype6-dev libjpeg-dev build-essential libopenjp2-7 libtiff5 nginx uwsgi-plugin-python3
pip3 install luma.core luma.oled luma.lcd netifaces gpiozero
sudo -H pip3 install flask
sudo cp ./nginx/default.conf /etc/nginx/conf.default
sudo systemctl restart nginx
sudo systemctl enable uwsgi
sudo systemctl start uwsgi
sudo cp ./sample.service /etc/systemd/system
sudo systemctl enable sample.service
sudo systemctl start sample.service
