FROM alpine:3.12

RUN apk add --no-cache python3 py3-pip &&\
    pip install --no-cache-dir --upgrade pip &&\
    pip install --no-cache-dir bitstring pyserial

WORKDIR /home/pi/wisun-gateway/