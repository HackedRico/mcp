from aiohttp import web
import logging

class McpAPI:

    def __init__(self, services):
        self.services = services
        self.mcp_svc = services.get("mcp_svc")
        self.log = logging.getLogger("plugins.mcp")
        self.log.info("[MCP] Initialized CalderaService")

    async def execute(self, request):
        self.log.info("[MCP] Executing request")
        
        try:
            data = await request.json()
            self.log.info(f"[MCP] Request data: {data}")
            user_input = data.get("text", "")
            self.log.info(f"[MCP] User data: {user_input}")
            model = data.get("type", "")
            self.log.info(f"[MCP] Model type: {model}")

            if not user_input:
                return web.json_response({"error": 'Missing "text" in request'}, status=400)

            result = await self.mcp_svc.execute(user_input)
            return web.json_response({"message": result})

        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
