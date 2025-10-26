#!/bin/sh

echo "=== 启动服务 ==="

# 先启动Xray服务
echo "启动Xray服务..."
/usr/local/bin/xray run -config /etc/xray/config.json &
XRAY_PID=$!

# 等待Xray完全启动
echo "等待Xray启动..."
sleep 10

# 检查Xray是否成功启动
if ! kill -0 $XRAY_PID 2>/dev/null; then
    echo "❌ Xray启动失败，检查配置..."
    # 显示Xray启动错误
    /usr/local/bin/xray run -config /etc/xray/config.json
    exit 1
fi

echo "✅ Xray启动成功，PID: $XRAY_PID"

# 再启动Python保活服务
echo "启动Python健康检查及保活服务..."
python3 /app/main.py &
PYTHON_PID=$!

echo "✅ 所有服务启动完成！"

# 简单的进程监控
while true; do
    if ! kill -0 $PYTHON_PID 2>/dev/null; then
        echo "❌ Python进程异常退出，重启中..."
        python3 /app/main.py &
        PYTHON_PID=$!
        echo "✅ Python服务已重启"
    fi

    if ! kill -0 $XRAY_PID 2>/dev/null; then
        echo "❌ Xray进程异常退出，重启中..."
        /usr/local/bin/xray run -config /etc/xray/config.json &
        XRAY_PID=$!
        sleep 10
        echo "✅ Xray服务已重启"
    fi
    
    sleep 30
done
