#!/usr/bin/env python3
from aiohttp import web
import sys
import subprocess
import time
import aiohttp
import asyncio

# 强制刷新输出缓冲区，确保日志能立即被看到
sys.stdout.flush()
sys.stderr.flush()

async def health_check(request):
    """健康检查端点，返回服务状态"""
    return web.json_response({
        "status": "ok", 
        "service": "xray-vless",
        "timestamp": time.time()  # 添加时间戳，使每次响应内容略有不同
    })

async def keep_alive_task():
    """关键的保活任务：每60秒访问一次自身的健康检查接口，模拟流量"""
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                # 访问自己服务上的健康检查接口
                async with session.get('http://localhost:8000/', timeout=5) as resp:
                    print(f"✅ 保活心跳发送成功，状态码: {resp.status}")
        except Exception as e:
            # 打印警告但不要退出循环，保活任务需要持续运行
            print(f"⚠️ 保活心跳发送失败: {e}")
        
        # 等待60秒（必须小于300秒的休眠阈值）
        await asyncio.sleep(60)

def print_node_info():
    """打印节点配置信息"""
    tcp_proxy_domain = "01.proxy.koyeb.app"
    uuid = "258751a7-eb14-47dc-8d18-511c3472220f"
    tcp_port = "15141"
    
    info = f"""
============================================================
🎯 VLESS节点配置信息 (已启用防休眠模式)
============================================================
📍 地址: {tcp_proxy_domain}
🔢 端口: {tcp_port}
🔑 UUID: {uuid}
🌐 协议: vless
📡 传输: websocket
🛣️  路径: /
🔒 安全: none (由Koyeb处理TLS)
💓 保活: 已启用 (每60秒一次心跳)
------------------------------------------------------------
🔗 分享链接:
vless://{uuid}@{tcp_proxy_domain}:{tcp_port}?type=ws&path=%2F#Koyeb-VLESS
============================================================
"""
    print(info, flush=True)

def create_app():
    """创建Web应用并配置路由"""
    app = web.Application()
    app.router.add_get('/', health_check)
    return app

async def start_background_tasks(app):
    """启动后台保活任务"""
    # 在应用启动时创建保活任务
    app['keep_alive'] = asyncio.create_task(keep_alive_task())

async def cleanup_background_tasks(app):
    """清理后台任务"""
    app['keep_alive'].cancel()
    try:
        await app['keep_alive']
    except asyncio.CancelledError:
        print("保活任务已安全退出。")

if __name__ == "__main__":
    print("🔄 开始启动服务...")
    print_node_info()
    
    print("🚀 启动Xray核心服务...")
    # 启动Xray进程
    xray_process = subprocess.Popen([
        "/usr/local/bin/xray", 
        "run", 
        "-config", 
        "/etc/xray/config.json"
    ])
    
    # 等待Xray完全启动
    time.sleep(3)
    
    port = 8000
    app = create_app()
    
    # 注册启动和清理回调函数
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    
    print(f"🩺 健康检查服务运行在端口: {port}")
    print("💓 防休眠保活心跳已激活（间隔60秒）")
    print("✅ 所有服务启动完成！")
    
    try:
        # 启动Web应用，注意设置print=None以避免aiohttp的默认日志刷屏
        web.run_app(app, host='0.0.0.0', port=port, print=None)
    except KeyboardInterrupt:
        print("收到中断信号，正在关闭服务...")
    finally:
        # 确保Python退出前终止Xray进程
        print("正在关闭Xray进程...")
        xray_process.terminate()
        xray_process.wait()
        print("服务已安全退出。")
