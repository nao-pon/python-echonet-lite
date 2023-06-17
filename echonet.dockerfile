FROM arm32v6/python:3-alpine3.14

RUN apk add --no-cache gcc git &&\
    pip install --no-cache-dir --upgrade pip &&\
    pip install --no-cache-dir luma.core luma.oled netifaces gpiozero bitstring numpy \
                               git+https://github.com/katsumin/luma.lcd.git@feature/st7789 && \
    apk del --purge gcc git

RUN mkdir -p /home/pi/wisun-gateway/

WORKDIR /home/pi/wisun-gateway/