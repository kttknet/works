#!/bin/sh

set -e

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "=== 启动服务 ==="

# 确保配置文件存在
log "检查配置文件..."
if [ -f /etc/xray/config.json ]; then
    log "✅ 配置文件存在"
else
    log "⚠️ 配置文件不存在，从/app/config.json复制..."
    mkdir -p /etc/xray/
    cp /app/config.json /etc/xray/config.json
    log "✅ 配置文件已复制"
fi

# 先启动Xray，等待它完全启动
log "启动Xray服务..."
/usr/local/bin/xray run -config /etc/xray/config.json &
XRAY_PID=$!
log "Xray启动完成，PID: $XRAY_PID"

# 等待Xray完全启动（重要！）
log "等待Xray服务初始化..."
sleep 15

if kill -0 $XRAY_PID 2>/dev/null; then
    log "✅ Xray启动成功"
else
    log "❌ Xray启动失败"
    exit 1
fi

# 启动Python保活服务
log "启动Python激进保活服务..."
python3 -u /app/main.py &
PYTHON_PID=$!
log "Python保活服务启动完成，PID: $PYTHON_PID"

sleep 5

if kill -0 $PYTHON_PID 2>/dev/null; then
    log "✅ Python保活服务启动成功"
else
    log "❌ Python保活服务启动失败"
    exit 1
fi

log "🎉 所有服务启动完成！开始监控..."

# 进程监控
while true; do
    if ! kill -0 $PYTHON_PID 2>/dev/null; then
        log "⚠️ Python进程异常，重启中..."
        python3 -u /app/main.py &
        PYTHON_PID=$!
        sleep 5
        log "✅ Python服务已重启"
    fi

    if ! kill -0 $XRAY_PID 2>/dev/null; then
        log "⚠️ Xray进程异常，重启中..."
        /usr/local/bin/xray run -config /etc/xray/config.json &
        XRAY_PID=$!
        sleep 15
        log "✅ Xray服务已重启"
    fi
    
    sleep 10
done
