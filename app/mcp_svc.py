import logging
import dspy
from app.utility.base_service import BaseService
from plugins.mcp.app.mcp_factory_client import run as factory_run
from plugins.mcp.app.mcp_planner_client import run as planner_run
from enum import Enum

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
        api_key = 12345
        self.lm = dspy.LM(
            model="gpt-4o",
            api_key=api_key,
            temperature=0.5,
        )
        self.log.info("[MCP] Initialized MCPService")

    async def execute(self, focus: str, prompt: str):
        def execute_factory(prompt, file: dict = None):
            """Factory function to create a tool function with closure."""
            return factory_run(prompt)
        
        def execute_planner(prompt: str, file: dict = None):
            """Factory function to create a tool function with closure."""
            return planner_run(prompt, file=file)

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
                result = await execute_planner(prompt, file)
            case ExecuteStyle.RAGfactory.value:
                result = await execute_factory(prompt, file)
            case _:
                self.log.error(f"[MCP] Unsupported execution style: {focus}")
                raise ValueError(f"Unsupported execution style: {focus}")
    
        
        self.log.info(f"[MCP] Executing prompt: {prompt}")
        # result = await run(prompt)

        # For now, we will mock the result since the actual run function is not implemented
        # In a real scenario, you would call the run function and await its result
        # result = await run(adversary_emulation_task=prompt)
        class MockResult:
            def __init__(self, message):
                self.process_result = message

        result = MockResult(
            f"[MOCKED] Pretend we created an adversary for task: '{prompt}'"
        )
        return result.process_result  # or return full result.toDict() if needed

