from aiohttp import web
from aiohttp_apispec import docs, request_schema, response_schema
import logging
import mlflow
import os
import json
from pathlib import Path
from datetime import datetime

# Import API schemas
from plugins.mcp.app.api.v2.schemas.base_schemas import *
from plugins.mcp.app.api.v2.schemas.execute_schemas import *
from plugins.mcp.app.api.v2.schemas.status_schemas import *
from plugins.mcp.app.api.v2.schemas.rag_schemas import *
from plugins.mcp.app.api.v2.schemas.runs_schemas import *

class McpAPI:

    def __init__(self, services):
        self.services = services
        self.mcp_svc = services.get("mcp_svc")
        self.log = logging.getLogger("plugins.mcp")
        self.log.info("[MCP] Initialized McpAPI")

    @docs(
        tags=["MCP / Ability Factory"],
        summary="Execute ability generation or operation planning",
        description="Generate Caldera abilities or plan operations using LLM. Supports 'factory' (ability generation), 'planner' (operation planning), and RAG-enhanced modes.",
    )
    @request_schema(ExecuteRequestSchema)
    @response_schema(ExecuteResponseSchema, 200)
    @response_schema(ErrorResponseSchema, 400)
    @response_schema(ErrorResponseSchema, 500)
    async def execute(self, request):
        self.log.info("[MCP] Executing request")
        try:
            data = await request.json()
            self.log.info(f"[MCP] Request data: {data}")
            user_input = data.get("text", "")
            self.log.info(f"[MCP] User input: {user_input}")
            focus = data.get("type", "factory")  # Default to factory if not specified
            self.log.info(f"[MCP] Execution focus: {focus}")
            model_config = data.get("config")
            self.log.info(f"[MCP] Config received")

            if not user_input:
                return web.json_response({"error": 'Missing "text" in request'}, status=400)

            # Pass both focus and prompt to the service
            result = await self.mcp_svc.execute(focus=focus, prompt=user_input, model_config=model_config)
            return web.json_response(result)

        except Exception as e:
            self.log.error(f"[MCP] Error executing request: {str(e)}")
            return web.json_response({"error": str(e)}, status=500)

    @docs(
        tags=["MCP / Execution Status"],
        summary="Get execution status",
        description="Retrieve the current status, reasoning trajectory, and results of a running or completed execution by run ID.",
    )
    @request_schema(StatusRequestSchema)
    @response_schema(StatusResponseSchema, 200)
    @response_schema(ErrorResponseSchema, 400)
    @response_schema(ErrorResponseSchema, 500)
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
            self.log.info(f"[MCP] Status for run {run_id} retrieved")

            return web.json_response(response)

        except Exception as e:
            self.log.error(f"[MCP] Error fetching run {run_id}: {e}")
            return web.json_response({"error": str(e)}, status=500)

    @docs(
        tags=["MCP / CTI Knowledge Base"],
        summary="Upload threat intelligence file",
        description="Upload a STIX JSON file containing Cyber Threat Intelligence for RAG-enhanced ability generation. Multipart form-data with 'file' field.",
    )
    @response_schema(UploadRagResponseSchema, 200)
    @response_schema(ErrorResponseSchema, 400)
    @response_schema(ErrorResponseSchema, 500)
    async def upload_rag(self, request):
        try:
            reader = await request.multipart()
            part = await reader.next()
            if not part or part.name != "file":
                return web.json_response({"error": 'Missing "file" field in form-data'}, status=400)

            raw_filename = part.filename or "rag.json"
            filename = os.path.basename(raw_filename)

            if not filename.lower().endswith(".json"):
                return web.json_response({"error": "Only .json files are allowed"}, status=400)

            base_dir = (Path(__file__).resolve().parent.parent / "data")
            base_dir.mkdir(parents=True, exist_ok=True)

            target_path = base_dir / filename
            if target_path.exists():
                ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                stem = Path(filename).stem
                suffix = Path(filename).suffix
                filename = f"{stem}_{ts}{suffix}"
                target_path = base_dir / filename

            file_bytes = await part.read()
            try:
                _ = json.loads(file_bytes.decode("utf-8"))
            except Exception as e:
                return web.json_response({"error": f"Invalid JSON: {e}"}, status=400)

            with open(target_path, "wb") as f:
                f.write(file_bytes)

            stat = target_path.stat()
            self.log.info(f"[MCP] Uploaded RAG file to {target_path} ({stat.st_size} bytes)")
            return web.json_response({
                "message": "RAG file uploaded",
                "filename": filename,
                "size": stat.st_size,
                "path": str(target_path)
            })
        except Exception as e:
            self.log.error(f"[MCP] Error uploading RAG file: {e}")
            return web.json_response({"error": str(e)}, status=500)

    @docs(
        tags=["MCP / CTI Knowledge Base"],
        summary="List threat intelligence files",
        description="Retrieve a list of all uploaded STIX CTI files with metadata (filename, size, last modified).",
    )
    @response_schema(ListRagResponseSchema, 200)
    @response_schema(ErrorResponseSchema, 500)
    async def list_rag(self, request):
        try:
            base_dir = (Path(__file__).resolve().parent.parent / "data")
            files = []
            if base_dir.exists():
                for p in base_dir.glob("*.json"):
                    try:
                        stat = p.stat()
                        files.append({
                            "filename": p.name,
                            "size": stat.st_size,
                            "modified": datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z"
                        })
                    except Exception:
                        continue
            return web.json_response({"files": sorted(files, key=lambda x: x["filename"].lower())})
        except Exception as e:
            self.log.error(f"[MCP] Error listing RAG files: {e}")
            return web.json_response({"error": str(e)}, status=500)

    @docs(
        tags=["MCP / Run History"],
        summary="List execution history",
        description="Browse all historical ability factory and operation planner executions with pagination. Returns run metadata, prompts, and results.",
    )
    @request_schema(ListRunsRequestSchema)
    @response_schema(ListRunsResponseSchema, 200)
    @response_schema(ErrorResponseSchema, 500)
    async def list_runs(self, request):
        """List all MLflow runs with basic information."""
        try:
            # Get optional query parameters for filtering/pagination
            limit = int(request.query.get("limit", 100))
            offset = int(request.query.get("offset", 0))

            client = mlflow.tracking.MlflowClient()

            # Get all experiments (in case there are multiple)
            experiments = client.search_experiments()

            all_runs = []
            for experiment in experiments:
                # Search runs in this experiment
                runs = client.search_runs(
                    experiment_ids=[experiment.experiment_id],
                    order_by=["start_time DESC"],
                    max_results=1000  # Get a large number, we'll paginate ourselves
                )

                for run in runs:
                    run_info = run.info
                    run_data = run.data

                    # Extract key information
                    run_record = {
                        "run_id": run_info.run_id,
                        "experiment_id": run_info.experiment_id,
                        "status": run_info.status,
                        "start_time": run_info.start_time,
                        "end_time": run_info.end_time,
                        "run_name": run_data.tags.get("mlflow.runName", "Unnamed Run"),
                        "prompt": run_data.params.get("prompt", ""),
                        "stage": run_data.tags.get("stage", ""),
                        "model": run_data.params.get("model", ""),
                        "process_result": run_data.params.get("process_result", ""),
                    }
                    all_runs.append(run_record)

            # Sort by start_time descending (newest first)
            all_runs.sort(key=lambda x: x["start_time"], reverse=True)

            # Apply pagination
            paginated_runs = all_runs[offset:offset + limit]

            return web.json_response({
                "runs": paginated_runs,
                "total": len(all_runs),
                "limit": limit,
                "offset": offset
            })
        except Exception as e:
            self.log.error(f"[MCP] Error listing runs: {e}")
            return web.json_response({"error": str(e)}, status=500)

    @docs(
        tags=["MCP / Run History"],
        summary="Get detailed run information",
        description="Get comprehensive details for a specific execution including full LLM reasoning trajectory, tool calls, parameters, and results.",
    )
    @response_schema(GetRunDetailResponseSchema, 200)
    @response_schema(ErrorResponseSchema, 400)
    @response_schema(ErrorResponseSchema, 500)
    async def get_run_detail(self, request):
        """Get detailed information for a specific run including full trajectory."""
        run_id = request.query.get("run_id")
        if not run_id:
            return web.json_response({"error": "Missing run_id"}, status=400)

        try:
            client = mlflow.tracking.MlflowClient()
            run = client.get_run(run_id)

            # Extract all trajectory data (thoughts, observations, tool calls)
            trajectory = {
                k: v for k, v in run.data.tags.items()
                if k.startswith("thought_") or k.startswith("observation_") or
                   k.startswith("tool_name_") or k.startswith("tool_args_")
            }

            # Build comprehensive response
            response = {
                "run_id": run_id,
                "status": run.info.status,
                "start_time": run.info.start_time,
                "end_time": run.info.end_time,
                "run_name": run.data.tags.get("mlflow.runName", "Unnamed Run"),
                "experiment_id": run.info.experiment_id,
                "params": dict(run.data.params),
                "tags": dict(run.data.tags),
                "trajectory": trajectory,
                "stage": run.data.tags.get("stage"),
                "reasoning": run.data.tags.get("reasoning"),
                "prompt": run.data.params.get("prompt"),
                "process_result": run.data.params.get("process_result"),
            }

            return web.json_response(response)
        except Exception as e:
            self.log.error(f"[MCP] Error fetching run detail {run_id}: {e}")
            return web.json_response({"error": str(e)}, status=500)

def setup_routes(app, mcp_api: McpAPI):
    app.router.add_post("/plugin/mcp/execute", mcp_api.execute)
    app.router.add_get("/plugin/mcp/status", mcp_api.status)
    app.router.add_post("/plugin/mcp/rag/upload", mcp_api.upload_rag)
    app.router.add_get("/plugin/mcp/rag/list", mcp_api.list_rag)