import os
import dspy
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json
import sys
import mlflow
from app.utility.base_world import BaseWorld
import traceback
from mlflow.tracking import MlflowClient
import asyncio
import copy

def get_llm_config():
    try:
        config = BaseWorld.strip_yml('plugins/mcp/conf/default.yml')[0]
        return config.get('llm', {})
    except Exception as e:
        print(f"[MCP] Failed to load LLM config: {e}")
        return {}

def configure_llm(llm_config, use_mock=False):
    if use_mock:
        class MockLM:
            def __call__(self, prompt):
                return "Mocked response"
        dspy.configure(lm=MockLM())
        return

    if llm_config.get("offline", False):
        os.environ["LITELLM_MODEL_METADATA_LOCAL_PATH"] = "/path/to/local.json"

    lm = {
        "model": llm_config.get("model", "gpt-4o"),
        "api_key": llm_config.get("api_key", ""),
        "api_base": llm_config.get("api_base")
    }
    
    dspy.configure(lm=lm)

def get_env():
    env = os.environ.copy()
    venv_site_packages = os.path.join(sys.prefix, "Lib", "site-packages")
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f"{venv_site_packages}:{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = venv_site_packages
    return env

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("caldera-mcp-FACTORY-client-1")
# mlflow.dspy.autolog()

current_dir = os.path.dirname(os.path.abspath(__file__))
server_params = StdioServerParameters(
    command="python",
    args=[current_dir+"/mcp_server.py"],
    env=get_env(),
)

class DSPyCalderaFactoryClient(dspy.Signature):
    """You are an ability factory for the Caldera adversary emulation platform.  You are given a list of tools to handle user requests and control Caldera via the
    MCP server for the Caldera API.  You will be given a user request and you will need to decide the right tools to use and use them accordingly
    to fulfill the user request.
    """

    adversary_emulation_task: str = dspy.InputField()
    process_result: str = dspy.OutputField(
        desc=(
            "Message that summarizes the result of the newly created adversary."
        )
    )

class DSPyCalderaFactoryClientWithRAG(dspy.Signature):
    """You are an ability factory for the Caldera adversary emulation platform enhanced with Cyber Threat Intelligence (CTI) data.
    You are given a list of tools to handle user requests and control Caldera via the MCP server for the Caldera API.
    You also have access to CTI context that provides information about attack patterns, malware, tools, threat actors, and techniques.
    Use the CTI context to create more accurate and realistic adversary emulations based on real-world threat intelligence.
    """

    adversary_emulation_task: str = dspy.InputField()
    cti_context: str = dspy.InputField(
        desc="Relevant CTI (Cyber Threat Intelligence) information including attack patterns, techniques, and threat actor behaviors"
    )
    process_result: str = dspy.OutputField(
        desc=(
            "Message that summarizes the result of the newly created adversary, "
            "including how CTI information was used to enhance the adversary profile."
        )
    )

# Factory function to create tool functions with proper closure
def create_tool_function(session, tool_name, tool_description):
    async def tool_function(**kwargs):
        mlflow.set_tag("stage", f"Tool.{tool_name}")
        result = await session.call_tool(tool_name, kwargs)
        return result
    tool_function.__doc__ = tool_description
    return tool_function

def format_rag_context(rag_context):
    """Format RAG context into a string for the DSPy signature."""
    if not rag_context:
        return "No CTI context available."
    
    formatted_parts = []
    
    # Add search results summary
    if "search_results" in rag_context:
        formatted_parts.append("Relevant CTI findings:")
        for i, result in enumerate(rag_context["search_results"][:3], 1):
            formatted_parts.append(f"{i}. {result}")
    
    # Add detailed context
    if "detailed_context" in rag_context:
        formatted_parts.append("\nDetailed CTI Information:")
        for ctx in rag_context["detailed_context"]:
            formatted_parts.append(f"\n{ctx['name']}:")
            formatted_parts.append(f"{ctx['description']}")
    
    return "\n".join(formatted_parts)

async def run(adversary_emulation_task: str, lm_obj = None, rag_context=None, run_id=None):
    # Build LM settings safely (support defaults)
    lm_settings = {}
    if lm_obj:
        lm_obj_safe = copy.deepcopy(lm_obj) or {}
        lm_settings = {
            "model": lm_obj_safe.get("model", "gpt-4o"),
            "api_key": lm_obj_safe.get("api_key", ""),
            "temperature": lm_obj_safe.get("temperature", 0.5),
            "max_tokens": lm_obj_safe.get("max_tokens", 10000),
        }
    else:
        llm_config = get_llm_config()
        lm_settings = {
            "model": llm_config.get("model", "gpt-4o"),
            "api_key": llm_config.get("api_key", ""),
            "temperature": llm_config.get("temperature", 0.5),
            "max_tokens": llm_config.get("max_tokens", 10000),
        }

    # Use the passed-in run_id to continue the MLflow run if provided
    created_local_run = False
    if not run_id:
        run = mlflow.start_run(run_name="MCP Ability Factory")
        run_id = run.info.run_id
        created_local_run = True

    mlflow.set_tag("status", "running")
    mlflow.set_tag("stage", "initializing")
    mlflow.log_param("prompt", adversary_emulation_task)

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize MCP session and list tools
                mlflow.set_tag("stage", "initializing MCP session")
                await session.initialize()

                mlflow.set_tag("stage", "listing tools")
                tools = await session.list_tools()

                # Use context to set LM for this task/run
                with dspy.context(lm=dspy.LM(
                    lm_settings['model'],
                    api_key=lm_settings['api_key'],
                    temperature=lm_settings['temperature'],
                    max_tokens=lm_settings['max_tokens']
                )):
                    mlflow.set_tag("stage", "creating DSPy ReAct instance")
                    dspy_tools = [dspy.Tool.from_mcp_tool(session, tool) for tool in tools.tools]

                    if rag_context:
                        signature = DSPyCalderaFactoryClientWithRAG
                        formatted_context = format_rag_context(rag_context)
                        react = dspy.ReAct(signature, tools=dspy_tools)
                        mlflow.set_tag("stage", "executing DSPy ReAct with RAG")
                        result = await react.acall(adversary_emulation_task=adversary_emulation_task, cti_context=formatted_context)
                    else:
                        signature = DSPyCalderaFactoryClient
                        react = dspy.ReAct(signature, tools=dspy_tools)
                        mlflow.set_tag("stage", "executing DSPy ReAct")
                        result = await react.acall(adversary_emulation_task=adversary_emulation_task)

                # Log outputs and trajectory
                mlflow.set_tag("stage", "completed")
                mlflow.set_tag("status", "complete")
                mlflow.set_tag("reasoning", result.reasoning)
                # Prefer param for process_result to match status API
                mlflow.log_param("process_result", result.process_result)
                # Keep tag for backward compatibility (optional)
                mlflow.set_tag("process_result", result.process_result)

                for k, v in result.trajectory.items():
                    mlflow.set_tag(k, json.dumps(v) if isinstance(v, (dict, list)) else str(v))

                mlflow.log_param("result_summary", result.process_result)

                print(json.dumps(result.toDict(), indent=4))

                # End the run only if we created it locally
                if created_local_run:
                    mlflow.end_run()

                return {"process_result": result.process_result}

    except Exception as e:
        tb = traceback.format_exc()
        print("[MCP] Exception occurred:")
        print(tb)
        mlflow.set_tag("status", "failed")
        mlflow.set_tag("stage", "error")
        mlflow.log_param("error", str(e))
        mlflow.log_param("traceback", tb)
        if created_local_run:
            mlflow.end_run()
        raise