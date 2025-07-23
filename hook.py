import os
import subprocess
import socket
import time
import traceback
import logging

from app.utility.base_world import BaseWorld

name = 'mcp'
description = 'Attachment for Model Context Protocol'
address = '/plugin/mcp/gui'
access = BaseWorld.Access.APP

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(('127.0.0.1', port)) == 0

# 🔁 Start MLflow server if it's not already running
if not is_port_open(5000):
    try:
        subprocess.Popen([
            "mlflow", "server",
            "--backend-store-uri", "sqlite:///mlruns.db",
            "--default-artifact-root", "./mlruns",
            "--host", "127.0.0.1",
            "--port", "5000"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[MCP] Starting MLflow server at http://localhost:5000")
    except Exception as e:
        print(f"[MCP] Failed to start MLflow server: {e}")
        traceback.print_exc()
else:
    print("[MCP] MLflow server already running on port 5000")

# 💤 Optional: Wait until server is reachable
for i in range(10):
    if is_port_open(5000):
        print("[MCP] MLflow is ready.")
        break
    time.sleep(1)
else:
    print("[MCP] MLflow failed to start within 10 seconds.")

# ✅ Now import modules that depend on MLflow
try:
    from plugins.mcp.app.mcp_svc import MCPService
    from plugins.mcp.app.mcp_gui import McpGUI
    from plugins.mcp.app.mcp_api import McpAPI
except ImportError as e:
    print(f"[MCP] Error importing MCP plugin modules: {e}")
    traceback.print_exc()

# ✅ Enable function stays the same
async def enable(services):
    app = services.get('app_svc').application

    services.get('data_svc').add_service('mcp_svc', MCPService(services))
    mcp_gui = McpGUI(services, name=name, description=description)
    app.router.add_static('/mcp', 'plugins/mcp/static/', append_version=True)
    
    mcp_api = McpAPI(services)
    app.router.add_route('POST', '/plugin/mcp/execute', mcp_api.execute)
