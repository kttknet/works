#!/bin/sh

# 函数：检查进程是否存活
check_process() {
    local pid=$1
    kill -0 $pid 2>/dev/null
    return $?
}

echo "启动Xray服务..."
/usr/local/bin/xray run -config /etc/xray/config.json &
XRAY_PID=$!

echo "等待Xray启动..."
sleep 5

echo "启动Python健康检查及保活服务..."
python3 /app/main.py &
PYTHON_PID=$!

echo "启动进程监控循环..."
# 简单的进程监控循环，每30秒检查一次
while true; do
    if ! check_process $PYTHON_PID; then
        echo "❌ Python进程（PID: $PYTHON_PID）异常退出，重启中..."
        python3 /app/main.py &
        PYTHON_PID=$!
        echo "✅ Python服务已重启，新PID: $PYTHON_PID"
    fi

    if ! check_process $XRAY_PID; then
        echo "❌ Xray进程（PID: $XRAY_PID）异常退出，重启中..."
        /usr/local/bin/xray run -config /etc/xray/config.json &
        XRAY_PID=$!
        echo "✅ Xray服务已重启，新PID: $XRAY_PID"
    fi

    # 每30秒检查一次
    sleep 30
done
