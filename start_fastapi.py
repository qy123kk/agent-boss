#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动FastAPI应用
"""

import uvicorn
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """启动FastAPI应用"""
    
    # 设置环境变量
    os.environ.setdefault("PYTHONPATH", str(project_root))
    
    # 启动配置
    config = {
        "app": "fastapi_app.main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": True,  # 开发模式
        "log_level": "info",
        "access_log": True,
        "workers": 1,  # 开发模式使用单进程
    }
    
    print("🚀 正在启动智能求职助手 FastAPI 服务...")
    print(f"📍 服务地址: http://{config['host']}:{config['port']}")
    print(f"📚 API文档: http://{config['host']}:{config['port']}/docs")
    print(f"📖 ReDoc文档: http://{config['host']}:{config['port']}/redoc")
    print("=" * 50)
    
    # 启动服务
    uvicorn.run(**config)


if __name__ == "__main__":
    main()
