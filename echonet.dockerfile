FROM alpine:3.12

RUN apk add --no-cache python3 alpine-sdk git linux-headers python3-dev py3-pip zlib-dev freetype-dev jpeg-dev tiff-dev openjpeg-dev &&\
    pip install --no-cache-dir --upgrade pip &&\
    pip install --no-cache-dir luma.core luma.oled netifaces gpiozero bitstring numpy \
                               git+https://github.com/katsumin/luma.lcd.git@feature/st7789 && \
    apk del --purge alpine-sdk git linux-headers python3-dev py3-pip zlib-dev freetype-dev jpeg-dev tiff-dev openjpeg-dev

RUN mkdir -p /home/pi/wisun-gateway/

WORKDIR /home/pi/wisun-gateway/