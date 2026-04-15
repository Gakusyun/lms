from app.main import app
import argparse
import sys

if __name__ == "__main__":
    # 处理 dev 命令：如果传入 dev 参数，开启 reload
    reload_mode = False
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        reload_mode = True
        # 移除 dev 参数，避免 argparse 解析报错
        sys.argv.pop(1)

    # 解析端口参数
    parser = argparse.ArgumentParser(description="FastAPI 启动脚本")
    parser.add_argument("--port", type=int, default=8000, help="服务端口号")
    args = parser.parse_args()
    
    # 启动服务
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=args.port,
        reload=reload_mode  # 根据 dev 参数自动开启重载
    )