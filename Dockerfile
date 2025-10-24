FROM alpine:latest

RUN apk update && apk add --no-cache \
    python3 \
    py3-aiohttp \
    curl \
    unzip \
    ca-certificates

RUN cd /tmp && \
    curl -L -o xray.zip https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip && \
    unzip xray.zip && \
    mv xray /usr/local/bin/ && \
    chmod +x /usr/local/bin/xray && \
    rm -rf xray.zip geoip.dat geosite.dat

WORKDIR /app

COPY config.json /etc/xray/config.json
COPY main.py .
COPY start.sh .

RUN chmod +x /app/start.sh

# 暴露17893和8000端口
EXPOSE 17893 8000

CMD ["/app/start.sh"]
