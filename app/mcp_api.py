from aiohttp import web
import logging

class McpAPI:

    def __init__(self, services):
        self.services = services
        self.mcp_svc = services.get("mcp_svc")
        self.log = logging.getLogger("plugins.mcp")
        self.log.info("[MCP] Initialized McpAPI")

    async def execute(self, request):
        self.log.info("[MCP] Executing request")
        try:
            data = await request.json()
            self.log.info(f"[MCP] Request data: {data}")
            user_input = data.get("text", "")
            self.log.info(f"[MCP] User input: {user_input}")
            focus = data.get("type", "factory")  # Default to factory if not specified
            self.log.info(f"[MCP] Execution focus: {focus}")

            if not user_input:
                return web.json_response({"error": 'Missing "text" in request'}, status=400)

            # Pass both focus and prompt to the service
            result = await self.mcp_svc.execute(focus=focus, prompt=user_input)
            return web.json_response({"message": result})

        except Exception as e:
            self.log.error(f"[MCP] Error executing request: {str(e)}")
            return web.json_response({"error": str(e)}, status=500)
