import logging
import dspy
from app.utility.base_service import BaseService
from plugins.mcp.app.mcp_factory_client import run as factory_run
from plugins.mcp.app.mcp_planner_client import run as planner_run
from plugins.mcp.app.rag import RAGService
from enum import Enum
import os
import mlflow
import asyncio
import json


class ExecuteStyle(Enum):
    LLMfactory = "factory"
    LLMplanner = "planner"
    RAGplanner = "rag_planner"
    RAGfactory = "rag_factory"


class MCPService(BaseService):
    def __init__(self, services):
        super().__init__()
        self.services = services
        self.data_svc = services.get("data_svc")
        self.file_svc = services.get("file_svc")
        self.auth_svc = services.get("auth_svc")
        self.log = logging.getLogger("plugins.mcp")

        # need to get api key from gui?
        api_key = "***REDACTED-OPENAI-KEY***"
        self.lm = dspy.LM(
            model="gpt-4o",
            api_key=api_key,
            temperature=0.5,
        )

        # Initialize RAG service
        self.log.info(f"[MCP] Initializing RAG")
        self.rag_service = None

        stix_bundle_path = os.path.join(os.getcwd(), "plugins", "mcp", "data", "stix_bundle.json")
        self.log.info(f"stix_bundle_path: {stix_bundle_path}")
        self.log.info(f"current_dir: {os.getcwd()}")
        if os.path.exists(stix_bundle_path):
            try:
                self.rag_service = RAGService(stix_bundle_path, api_key=api_key, log=self.log)
                self.log.info("[MCP] RAG service initialized with STIX bundle")
            except Exception as e:
                self.log.warning(f"[MCP] Failed to initialize RAG service: {e}")
        else:
            self.log.warning(f"[MCP] STIX bundle not found at {stix_bundle_path}")


        self.log.info("[MCP] Initialized MCPService")

    async def execute(self, focus: str, prompt: str, file: dict = None):
        """Start MLflow run and launch async execution."""
        run = mlflow.start_run(run_name="MCP Execution")
        run_id = run.info.run_id
        mlflow.end_run()  # Immediately end run so polling can begin

        # Optional: collect RAG context
        rag_context = None
        if focus in [ExecuteStyle.RAGplanner.value, ExecuteStyle.RAGfactory.value] and self.rag_service:
            try:
                rag_context = self.rag_service.get_context_for_task(prompt)
                self.log.info("[MCP] RAG context retrieved")
            except Exception as e:
                self.log.warning(f"[MCP] RAG context error: {e}")

        # Run logic in background
        asyncio.create_task(self._run_execution(focus, prompt, rag_context, run_id))

        return {"run_id": run_id}

    async def _run_execution(self, focus, prompt, rag_context, run_id):
        """Executes the full DSPy logic in background and tracks via MLflow."""
        try:
            # Force clear any stale MLflow context from main thread
            mlflow.end_run()
            with mlflow.start_run(run_id=run_id):
                mlflow.set_tag("stage", "initializing")
                mlflow.log_param("prompt", prompt)

                if focus == ExecuteStyle.LLMfactory.value:
                    self.log.info(f"[MCP] Executing factory with prompt: {prompt}")
                    result = await factory_run(prompt, run_id=run_id)

                elif focus == ExecuteStyle.LLMplanner.value:
                    self.log.info(f"[MCP] Executing planner with prompt: {prompt}")
                    result = await planner_run(prompt, run_id=run_id)

                elif focus == ExecuteStyle.RAGplanner.value:
                    self.log.info(f"[MCP] Executing RAG-enhanced planner with prompt: {prompt}")
                    # Log RAG context into MLflow
                    if rag_context:
                        for i, thought in enumerate(rag_context.get("thoughts", [])):
                            mlflow.set_tag(f"thought_{i}", thought)
                        mlflow.set_tag("tool_name_0", "get_context_for_task")
                        mlflow.set_tag("tool_args_0", json.dumps({"query": prompt}))
                    result = await planner_run(prompt, rag_context=rag_context, run_id=run_id)

                elif focus == ExecuteStyle.RAGfactory.value:
                    self.log.info(f"[MCP] Executing RAG-enhanced factory with prompt: {prompt}")
                    # Log RAG context into MLflow
                    if rag_context:
                        for i, thought in enumerate(rag_context.get("thoughts", [])):
                            mlflow.set_tag(f"thought_{i}", thought)
                        mlflow.set_tag("tool_name_0", "get_context_for_task")
                        mlflow.set_tag("tool_args_0", json.dumps({"query": prompt}))
                    result = await factory_run(prompt, rag_context=rag_context, run_id=run_id)

                else:
                    raise ValueError(f"Unsupported execution style: {focus}")

                mlflow.set_tag("stage", "complete")
                mlflow.set_tag("status", "success")
                mlflow.log_param("result", json.dumps(result.get("process_result", {})))

        except Exception as e:
            self.log.error(f"[MCP] Execution failed: {e}")
            mlflow.set_tag("stage", "error")
            mlflow.set_tag("status", "error")
            mlflow.log_param("error", str(e))

        finally:
            mlflow.end_run()