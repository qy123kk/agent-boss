#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的连接测试
"""

import requests
import socket
import time


def check_port(host='localhost', port=8000):
    """检查端口是否开放"""
    print(f"🔍 检查端口 {host}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print(f"✅ 端口 {port} 开放")
            return True
        else:
            print(f"❌ 端口 {port} 未开放")
            return False
    except Exception as e:
        print(f"❌ 端口检查异常: {e}")
        return False


def simple_health_check():
    """简单的健康检查"""
    print("🏥 执行简单健康检查...")
    try:
        # 设置较短的超时时间
        response = requests.get("http://localhost:8000/health", timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {response.elapsed.total_seconds():.2f}秒")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查成功")
            print(f"服务状态: {data.get('status')}")
            print(f"初始化状态: {data.get('initialized')}")
            print(f"版本: {data.get('version')}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误 - 服务可能未启动")
        return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False


def test_root_page():
    """测试根页面"""
    print("\n🏠 测试根页面...")
    try:
        response = requests.get("http://localhost:8000/", timeout=10)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ 根页面访问成功")
            print(f"内容类型: {response.headers.get('content-type')}")
            return True
        else:
            print(f"❌ 根页面访问失败")
            return False
    except Exception as e:
        print(f"❌ 根页面测试异常: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始简单连接测试")
    print("=" * 40)
    
    # 1. 检查端口
    if not check_port():
        print("\n❌ FastAPI服务可能未启动")
        print("💡 请确保运行了: python start_fastapi.py")
        return
    
    # 2. 健康检查
    print()
    if not simple_health_check():
        print("\n❌ 健康检查失败")
        return
    
    # 3. 测试根页面
    if not test_root_page():
        print("\n❌ 根页面测试失败")
        return
    
    print("\n" + "=" * 40)
    print("🎉 基础连接测试通过！")
    print("\n📋 可用的API端点:")
    print("   - 健康检查: http://localhost:8000/health")
    print("   - API文档: http://localhost:8000/docs")
    print("   - ReDoc: http://localhost:8000/redoc")
    print("   - 对话API: http://localhost:8000/api/v1/conversation/")
    print("   - RAG API: http://localhost:8000/api/v1/rag/")


if __name__ == "__main__":
    main()
