from aiohttp import web

class McpAPI:

    def __init__(self, services):
        self.services = services
        self.mcp_svc = services.get('mcp_svc')

    async def execute(self, request):
        try:
            data = await request.json()
            user_input = data.get('text', '')

            if not user_input:
                return web.json_response({'error': 'Missing "text" in request'}, status=400)

            result = await self.mcp_svc.execute(user_input)
            return web.json_response({'message': result})

        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
