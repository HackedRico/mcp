import logging
import dspy
from app.utility.base_service import BaseService
from plugins.mcp.app.mcp_factory_client import run as factory_run
from plugins.mcp.app.mcp_planner_client import run as planner_run
from plugins.mcp.app.rag import RAGService
from enum import Enum
import os

# from plugins.mcp.app.mcp_factory_client import run  # async def run(user_input: str)


# create dspy config like in alteration pipeline and in bloodhound from here

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
        """Execute MCP operations with optional RAG context."""

        # Get RAG context if using RAG-enhanced execution

        rag_context = None
        if focus in [ExecuteStyle.RAGplanner.value, ExecuteStyle.RAGfactory.value]:
            self.log.info(f"RAG? {focus}")
            self.log.info(f"rag_service: {self.rag_service}")
            if self.rag_service:
                self.log.info(f"bruh")
                rag_context = self.rag_service.get_context_for_task(prompt)
                self.log.info(f"bruh1")
                self.log.info(f"[MCP] Retrieved RAG context for task: {prompt}")
            else:
                self.log.warning("[MCP] RAG requested but service not initialized")

        async def execute_factory(prompt, rag_context=None):
            """Factory function to create a tool function with closure."""
            self.log.info(f"rag_context: {rag_context}")
            return await factory_run(prompt, rag_context=rag_context)

        async def execute_planner(prompt: str, rag_context=None):
            """Factory function to create a tool function with closure."""
            return await planner_run(prompt, rag_context=rag_context)

        self.log.info(f"[MCP] Execution style: {focus}")
        self.log.info(f"[MCP] Prompt: {prompt}")

        #switch from gui? focus need to be compiled at gui for this approach to work
        match focus:
            case ExecuteStyle.LLMfactory.value:
                self.log.info(f"[MCP] Executing factory with prompt: {prompt}")
                result = await execute_factory(prompt)
            case ExecuteStyle.LLMplanner.value:
                self.log.info(f"[MCP] Executing planner with prompt: {prompt}")
                result = await execute_planner(prompt)
            case ExecuteStyle.RAGplanner.value:
                self.log.info(f"[MCP] Executing RAG-enhanced planner with prompt: {prompt}")
                result = await execute_planner(prompt, rag_context=rag_context)
            case ExecuteStyle.RAGfactory.value:
                self.log.info(f"[MCP] Executing RAG-enhanced factory with prompt: {prompt}")
                result = await execute_factory(prompt, rag_context=rag_context)
            case _:
                self.log.error(f"[MCP] Unsupported execution style: {focus}")
                raise ValueError(f"Unsupported execution style: {focus}")

        # Return the actual result instead of mock
        if hasattr(result, 'process_result'):
            return result.process_result
        else:
            return str(result)  # Fallback for different result types