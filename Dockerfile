FROM alpine:3.18

RUN apk update && apk add --no-cache \
    python3 \
    py3-pip \
    curl \
    unzip \
    ca-certificates \
    tzdata

RUN pip3 install --no-cache-dir aiohttp==3.9.0

RUN cd /tmp && \
    curl -L -o xray.zip https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip && \
    unzip xray.zip && \
    mv xray /usr/local/bin/ && \
    chmod +x /usr/local/bin/xray && \
    mkdir -p /usr/local/share/xray/ && \
    mv geoip.dat geosite.dat /usr/local/share/xray/ && \
    rm -f xray.zip

WORKDIR /app

COPY . .

RUN mkdir -p /etc/xray/ && \
    cp config.json /etc/xray/config.json && \
    chmod +x start.sh

EXPOSE 15141 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["./start.sh"]
