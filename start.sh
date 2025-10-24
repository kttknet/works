#!/bin/sh
echo "启动Xray服务..."
/usr/local/bin/xray run -config /etc/xray/config.json &
echo "等待Xray启动..."
sleep 5
echo "启动Python健康检查..."
python3 /app/main.py
