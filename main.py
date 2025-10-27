#!/usr/bin/env python3
from aiohttp import web
import sys
import aiohttp
import asyncio
import random
import time
import datetime
import urllib.parse
import json
import ssl

# 强制刷新输出缓冲区
sys.stdout = open(1, 'w', buffering=1)
sys.stderr = open(2, 'w', buffering=1)
sys.stdout.flush()
sys.stderr.flush()

CONFIG = {
    "domain": "select-buzzard-getnode-c0cddf87.koyeb.app",
    "port": "443",
    "uuid": "258751a7-eb14-47dc-8d18-511c3472220f",
    "internal_port": 8000,
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15",
        "Mozilla/5.0 (Android 12; Mobile; rv:90.0) Gecko/20100101 Firefox/90.0"
    ]
}

# 全局变量
request_counter = 0
start_time = time.time()
domain_accessible = False
domain_fail_count = 0
last_successful_domain_check = 0

def log_message(message):
    """增强的日志函数"""
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    full_message = f"[{timestamp}] {message}"
    print(full_message, flush=True)

# 三种精美的仿真页面模板（完整保留）
SIMULATED_PAGES = [
    {
        "title": "服务状态监控中心",
        "content": """
        <div class="status-container">
            <h2>🔄 服务状态监控中心</h2>
            <div class="status-grid">
                <div class="status-card">
                    <div class="status-icon">✅</div>
                    <div class="status-info">
                        <div class="status-label">服务状态</div>
                        <div class="status-value online">正常运行</div>
                    </div>
                </div>
                <div class="status-card">
                    <div class="status-icon">📊</div>
                    <div class="status-info">
                        <div class="status-label">请求统计</div>
                        <div class="status-value">{requests} 次访问</div>
                    </div>
                </div>
                <div class="status-card">
                    <div class="status-icon">⏱️</div>
                    <div class="status-info">
                        <div class="status-label">运行时间</div>
                        <div class="status-value">{uptime}</div>
                    </div>
                </div>
                <div class="status-card">
                    <div class="status-icon">🔄</div>
                    <div class="status-info">
                        <div class="status-label">最后更新</div>
                        <div class="status-value">{timestamp}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        "style": """
        .status-container { max-width: 900px; margin: 50px auto; padding: 30px; }
        .status-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .status-card { 
            background: white; padding: 25px; border-radius: 15px; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.1); display: flex; 
            align-items: center; transition: transform 0.3s; 
        }
        .status-card:hover { transform: translateY(-5px); }
        .status-icon { font-size: 2.5em; margin-right: 20px; }
        .status-info { flex: 1; }
        .status-label { font-size: 0.9em; color: #666; margin-bottom: 5px; }
        .status-value { font-size: 1.3em; font-weight: bold; color: #333; }
        .online { color: #28a745; }
        """
    },
    {
        "title": "系统性能监控面板",
        "content": """
        <div class="monitor-container">
            <h2>📊 系统性能监控面板</h2>
            <div class="metrics-container">
                <div class="metric">
                    <div class="metric-header">
                        <span class="metric-title">CPU使用率</span>
                        <span class="metric-value">{cpu}%</span>
                    </div>
                    <div class="metric-bar">
                        <div class="metric-fill cpu-fill" style="width: {cpu}%"></div>
                    </div>
                </div>
                <div class="metric">
                    <div class="metric-header">
                        <span class="metric-title">内存使用</span>
                        <span class="metric-value">{memory}%</span>
                    </div>
                    <div class="metric-bar">
                        <div class="metric-fill memory-fill" style="width: {memory}%"></div>
                    </div>
                </div>
                <div class="metric">
                    <div class="metric-header">
                        <span class="metric-title">网络流量</span>
                        <span class="metric-value">{network}%</span>
                    </div>
                    <div class="metric-bar">
                        <div class="metric-fill network-fill" style="width: {network}%"></div>
                    </div>
                </div>
            </div>
            <div class="performance-stats">
                <div class="stat">
                    <div class="stat-number">{requests}</div>
                    <div class="stat-label">总请求数</div>
                </div>
                <div class="stat">
                    <div class="stat-number">99.8%</div>
                    <div class="stat-label">服务可用率</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{uptime}</div>
                    <div class="stat-label">持续运行</div>
                </div>
            </div>
        </div>
        """,
        "style": """
        .monitor-container { max-width: 800px; margin: 50px auto; padding: 30px; }
        .metrics-container { margin: 30px 0; }
        .metric { margin: 25px 0; }
        .metric-header { 
            display: flex; justify-content: space-between; 
            margin-bottom: 10px; font-weight: bold; 
        }
        .metric-bar { 
            width: 100%; height: 12px; background: #f0f0f0; 
            border-radius: 6px; overflow: hidden; 
        }
        .metric-fill { 
            height: 100%; transition: width 0.5s; border-radius: 6px;
        }
        .cpu-fill { background: linear-gradient(90deg, #ff6b6b, #ff8e8e); }
        .memory-fill { background: linear-gradient(90deg, #4ecdc4, #88d3ce); }
        .network-fill { background: linear-gradient(90deg, #45b7d1, #96cfe3); }
        .performance-stats { 
            display: flex; justify-content: space-around; 
            margin-top: 40px; 
        }
        .stat { text-align: center; }
        .stat-number { 
            font-size: 2.5em; font-weight: bold; color: #2c3e50; 
            margin-bottom: 5px; 
        }
        .stat-label { color: #7f8c8d; font-size: 0.9em; }
        """
    },
    {
        "title": "API网关控制台",
        "content": """
        <div class="api-container">
            <h2>🚀 API网关控制台</h2>
            <div class="dashboard">
                <div class="api-status">
                    <h3>服务状态概览</h3>
                    <div class="status-badges">
                        <span class="badge success">网关服务: 运行中</span>
                        <span class="badge success">健康检查: 通过</span>
                        <span class="badge success">代理服务: 活跃</span>
                        <span class="badge info">请求数: {requests}</span>
                    </div>
                </div>
                <div class="endpoints-list">
                    <h3>可用API端点</h3>
                    <div class="endpoint-item">
                        <span class="method get">GET</span>
                        <span class="path">/api/health</span>
                        <span class="description">服务健康状态检查</span>
                    </div>
                    <div class="endpoint-item">
                        <span class="method get">GET</span>
                        <span class="path">/api/stats</span>
                        <span class="description">系统性能统计信息</span>
                    </div>
                    <div class="endpoint-item">
                        <span class="method get">GET</span>
                        <span class="path">/api/version</span>
                        <span class="description">服务版本信息</span>
                    </div>
                    <div class="endpoint-item">
                        <span class="method get">GET</span>
                        <span class="path">/status</span>
                        <span class="description">实时服务状态</span>
                    </div>
                </div>
            </div>
            <div class="monitoring-data">
                <div class="data-card">
                    <h4>实时监控数据</h4>
                    <ul>
                        <li>当前时间: {timestamp}</li>
                        <li>运行时长: {uptime}</li>
                        <li>内存占用: {memory}%</li>
                        <li>CPU负载: {cpu}%</li>
                    </ul>
                </div>
            </div>
        </div>
        """,
        "style": """
        .api-container { max-width: 1000px; margin: 50px auto; padding: 30px; }
        .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
        .status-badges { display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0; }
        .badge { 
            padding: 8px 15px; border-radius: 20px; font-size: 0.9em; 
            font-weight: bold; 
        }
        .success { background: #d4edda; color: #155724; }
        .info { background: #d1ecf1; color: #0c5460; }
        .endpoints-list { margin-top: 20px; }
        .endpoint-item { 
            display: flex; align-items: center; padding: 12px; 
            background: #f8f9fa; margin: 8px 0; border-radius: 8px; 
        }
        .method { 
            padding: 4px 10px; border-radius: 4px; font-weight: bold; 
            margin-right: 15px; min-width: 50px; text-align: center; 
        }
        .get { background: #61affe; color: white; }
        .path { font-family: monospace; color: #0d6efd; flex: 1; }
        .description { color: #6c757d; }
        .monitoring-data { margin-top: 30px; }
        .data-card { background: #f8f9fa; padding: 20px; border-radius: 10px; }
        .data-card ul { list-style: none; padding: 0; }
        .data-card li { padding: 5px 0; border-bottom: 1px solid #dee2e6; }
        """
    }
]

def generate_simulated_page():
    """生成精美的仿真页面"""
    global request_counter
    request_counter += 1
    
    page_template = random.choice(SIMULATED_PAGES)
    
    uptime_seconds = int(time.time() - start_time)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    uptime_str = f"{hours}小时{minutes}分钟"
    
    cpu_usage = random.randint(15, 45)
    memory_usage = random.randint(40, 75)
    network_usage = random.randint(20, 60)
    
    content = page_template["content"].format(
        timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        requests=request_counter,
        uptime=uptime_str,
        cpu=cpu_usage,
        memory=memory_usage,
        network=network_usage
    )
    
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{page_template["title"]}</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            body {{
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #2d3748;
                min-height: 100vh;
                padding: 20px;
                line-height: 1.6;
            }}
            h1, h2, h3, h4 {{
                color: #2d3748;
                margin-bottom: 1rem;
                font-weight: 600;
            }}
            h2 {{
                font-size: 2rem;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 0.5rem;
                margin-bottom: 2rem;
            }}
            {page_template["style"]}
            .footer {{
                text-align: center;
                margin-top: 3rem;
                color: rgba(255,255,255,0.8);
                font-size: 0.9rem;
                padding: 1rem;
            }}
            @media (max-width: 768px) {{
                .status-grid, .dashboard {{
                    grid-template-columns: 1fr;
                }}
                .performance-stats {{
                    flex-direction: column;
                    gap: 20px;
                }}
            }}
        </style>
    </head>
    <body>
        {content}
        <div class="footer">
            <p>✨ 自动生成页面 • 最后更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • 请求ID: {random.randint(1000,9999)}</p>
        </div>
    </body>
    </html>
    """
    return html

async def health_check(request):
    """健康检查端点"""
    global request_counter
    request_counter += 1
    
    path = request.path
    
    if path == '/api/health':
        return web.json_response({
            "status": "healthy",
            "service": "api-gateway",
            "timestamp": datetime.datetime.now().isoformat(),
            "version": "1.0",
            "requests": request_counter,
            "uptime": int(time.time() - start_time),
            "domain_accessible": domain_accessible,
            "domain_fail_count": domain_fail_count,
            "last_successful_check": last_successful_domain_check
        })
    elif path == '/api/stats':
        return web.json_response({
            "uptime": int(time.time() - start_time),
            "requests": request_counter,
            "active_connections": random.randint(50, 200),
            "memory_usage": random.randint(40, 75),
            "cpu_usage": random.randint(15, 45),
            "domain_status": "accessible" if domain_accessible else "unreachable",
            "fail_count": domain_fail_count
        })
    elif path == '/api/version':
        return web.json_response({
            "name": "API Gateway",
            "version": "1.0.0",
            "build": "b69a376",
            "timestamp": datetime.datetime.now().isoformat()
        })
    elif path == '/ping':
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        uptime_seconds = int(time.time() - start_time)
        
        response_data = {
            "status": "alive",
            "service": "Koyeb Proxy Service",
            "timestamp": current_time,
            "uptime_seconds": uptime_seconds,
            "requests_handled": request_counter,
            "domain_accessible": domain_accessible,
            "domain_fail_count": domain_fail_count,
            "ping_id": random.randint(1000, 9999),
            "message": "✅ Service is active and responsive"
        }
        
        log_message(f"🏓 保活端点被访问 - Ping ID: {response_data['ping_id']}")
        return web.json_response(response_data)
    
    html_content = generate_simulated_page()
    return web.Response(text=html_content, content_type='text/html')

async def direct_port_keep_alive():
    """直接端口保活"""
    try:
        url = f'http://127.0.0.1:{CONFIG["internal_port"]}/health'
        async with aiohttp.ClientSession() as session:
            headers = {'User-Agent': random.choice(CONFIG['user_agents'])}
            async with session.get(url, headers=headers, timeout=5) as resp:
                log_message(f"🔧 端口保活成功: {resp.status} (端口{CONFIG['internal_port']})")
                return True
    except Exception as e:
        log_message(f"⚠️ 端口保活失败: {str(e)[:50]}")
        return False

async def external_domain_keep_alive():
    """通过公网域名的保活 - 增强版本"""
    global domain_accessible, domain_fail_count, last_successful_domain_check
    
    try:
        paths = ['/', '/health', '/status', '/api/health', '/api/stats', '/ping']
        path = random.choice(paths)
        url = f'https://{CONFIG["domain"]}{path}'
        
        # 创建忽略SSL验证的连接器
        connector = aiohttp.TCPConnector(ssl=False)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            headers = {
                'User-Agent': random.choice(CONFIG['user_agents']),
                'Accept': 'application/json,text/html',
                'Cache-Control': 'no-cache'
            }
            
            async with session.get(url, headers=headers, timeout=15) as resp:
                status_info = f"{resp.status}"
                if path.startswith('/api') or path == '/ping':
                    try:
                        data = await resp.json()
                        status_info = f"{resp.status} {str(data)[:30]}..."
                    except:
                        pass
                
                log_message(f"🌐 域名保活成功: {status_info} {path}")
                domain_accessible = True
                last_successful_domain_check = time.time()
                if domain_fail_count > 0:
                    domain_fail_count = 0
                return True
                
    except asyncio.TimeoutError:
        domain_fail_count += 1
        log_message(f"⏰ 域名保活超时 (失败次数: {domain_fail_count})")
        domain_accessible = False
        return False
    except aiohttp.ClientConnectorError as e:
        domain_fail_count += 1
        log_message(f"🔌 域名连接错误: {str(e)[:50]} (失败次数: {domain_fail_count})")
        domain_accessible = False
        return False
    except Exception as e:
        domain_fail_count += 1
        log_message(f"⚠️ 域名保活异常: {str(e)[:50]} (失败次数: {domain_fail_count})")
        domain_accessible = False
        return False

async def internal_keep_alive():
    """内部健康检查"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'http://127.0.0.1:{CONFIG["internal_port"]}/health',
                timeout=3
            ) as resp:
                log_message("💚 内部健康检查成功")
                return True
    except Exception as e:
        log_message(f"⚠️ 内部检查失败: {str(e)[:30]}")
        return False

async def smart_keep_alive():
    """智能保活策略 - 优化版本"""
    cycle_count = 0
    
    # 等待服务完全启动
    await asyncio.sleep(10)
    log_message("🚀 开始智能保活策略")
    
    while True:
        try:
            # 1. 内部健康检查（最高优先级，每次执行）
            await internal_keep_alive()
            
            # 2. 直接端口保活（高频）
            if cycle_count % 2 == 0:
                await direct_port_keep_alive()
            
            # 3. 外部域名保活（智能调整频率）
            domain_check_interval = 3  # 默认每3次循环检查一次
            
            # 如果连续失败，减少检查频率
            if domain_fail_count > 5:
                domain_check_interval = 6
            elif domain_fail_count > 10:
                domain_check_interval = 10
                
            if cycle_count % domain_check_interval == 0:
                await external_domain_keep_alive()
            
            # 动态调整间隔
            base_interval = 6
            if domain_fail_count > 0:
                base_interval = min(12, base_interval + domain_fail_count // 2)
            
            sleep_time = random.randint(base_interval, base_interval + 3)
            log_message(f"⏰ 下次保活: {sleep_time}秒后 (失败次数: {domain_fail_count})")
            await asyncio.sleep(sleep_time)
            
            cycle_count += 1
            
        except Exception as e:
            log_message(f"💥 保活异常: {str(e)[:30]}")
            await asyncio.sleep(8)

def create_app():
    app = web.Application()
    # 注册所有路由
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    app.router.add_get('/status', health_check)
    app.router.add_get('/api/health', health_check)
    app.router.add_get('/api/stats', health_check)
    app.router.add_get('/api/version', health_check)
    app.router.add_get('/ping', health_check)
    return app

async def start_background_tasks(app):
    # 延迟启动保活任务
    await asyncio.sleep(8)
    app['keep_alive'] = asyncio.create_task(smart_keep_alive())

async def cleanup_background_tasks(app):
    if 'keep_alive' in app:
        app['keep_alive'].cancel()
        try:
            await app['keep_alive']
        except asyncio.CancelledError:
            log_message("保活任务已安全停止")

if __name__ == "__main__":
    log_message("🚀 启动智能防休眠服务")
    log_message("🎯 目标: 确保Koyeb检测到流量")
    log_message("⏱️ 保活间隔: 动态调整")
    log_message("🔧 关键修复: 增强域名保活稳定性")
    log_message("🌐 公网域名: select-buzzard-getnode-c0cddf87.koyeb.app")
    log_message("🎨 仿真页面: 三种精美模板已启用")
    log_message("🏓 新增: 专用保活端点 /ping")
    log_message("🛡️ 增强: SSL验证忽略和智能重试机制")
    
    app = create_app()
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    
    web.run_app(app, host='0.0.0.0', port=CONFIG['internal_port'], print=None)
