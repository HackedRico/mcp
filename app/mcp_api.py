from aiohttp import web
import logging
import mlflow

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
            return web.json_response(result)


        except Exception as e:
            self.log.error(f"[MCP] Error executing request: {str(e)}")
            return web.json_response({"error": str(e)}, status=500)

    async def status(self, request):
        run_id = request.query.get("run_id")
        if not run_id:
            return web.json_response({"error": "Missing run_id"}, status=400)
        try:
            client = mlflow.tracking.MlflowClient()
            run = client.get_run(run_id)
            
             # Extract full trajectory
            trajectory = {
                k: v for k, v in run.data.tags.items()
                if k.startswith("thought_") or k.startswith("observation_") or k.startswith("tool_name_") or k.startswith("tool_args_")
            }
            

            response = {
                "run_id": run_id,
                "status": run.info.status,
                "stage": run.data.tags.get("stage"),
                "prompt": run.data.params.get("prompt"),
                "reasoning": run.data.tags.get("reasoning"),
                "process_result": run.data.params.get("process_result"),
                "trajectory": trajectory
            }
            self.log.info(f"[MCP] Status for run {run_id}: {response}")

            return web.json_response(response)

        except Exception as e:
            self.log.error(f"[MCP] Error fetching run {run_id}: {e}")
            return web.json_response({"error": str(e)}, status=500)
