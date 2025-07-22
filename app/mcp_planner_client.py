import os
import dspy
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json
import sys
import mlflow
from app.utility.base_world import BaseWorld

def get_llm_config():
    try:
        config = BaseWorld.strip_yml('plugins/mcp/conf/default.yml')[0]
        return config.get('llm', {})
    except Exception as e:
        print(f"[MCP] Failed to load LLM config: {e}")
        return {}

def configure_llm(llm_config):
    if llm_config.get("offline", False):
        os.environ["LITELLM_MODEL_METADATA_LOCAL_PATH"] = "/path/to/local.json"
    
    lm = dspy.LM(
        model=llm_config.get("model", "gpt-4o"),
        api_key=llm_config.get("api_key", ""),
        api_base=llm_config.get("api_base")
    )
    dspy.configure(lm=lm)

# Configure LLM from config
llm_config = get_llm_config()
configure_llm(llm_config)

env = os.environ.copy()
venv_site_packages = os.path.join(sys.prefix, "Lib", "site-packages")
if 'PYTHONPATH' in env:
    env['PYTHONPATH'] = f"{venv_site_packages}:{env['PYTHONPATH']}"
else:
    env['PYTHONPATH'] = venv_site_packages


mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("caldera-mcp-client-1")
mlflow.dspy.autolog()
current_dir = os.path.dirname(os.path.abspath(__file__))

server_params = StdioServerParameters(
    command="python",
    args=[current_dir+"/mcp_server.py"],
    env=env,
)


class DSPyCalderaPlannerClient(dspy.Signature):
    """You are a planner for the Caldera adversary emulation platform.  You are given a list of tools to handle user requests and control Caldera via the
    MCP server for the Caldera API.  You will be given a user request and you will need to decide the right tools to use and use them accordinly
    to fulfill the user request and conduct an adversary emulation operation.
    """

    adversary_emulation_task: str = dspy.InputField()
    process_result: str = dspy.OutputField(
        desc=(
            "Message that summarizes the result of the adversary emulation operation."
        )
    )


class DSPyCalderaPlannerClientWithRAG(dspy.Signature):
    """You are a planner for the Caldera adversary emulation platform enhanced with Cyber Threat Intelligence (CTI) data.
    You are given a list of tools to handle user requests and control Caldera via the MCP server for the Caldera API.
    You also have access to CTI context that provides information about attack patterns, malware, tools, threat actors, and techniques.
    Use the CTI context to plan more realistic and comprehensive adversary emulation operations based on real-world threat intelligence.
    When planning operations, consider the attack patterns and techniques used by real threat actors to create more authentic scenarios.
    """

    adversary_emulation_task: str = dspy.InputField()
    cti_context: str = dspy.InputField(
        desc="Relevant CTI (Cyber Threat Intelligence) information including attack patterns, techniques, and threat actor behaviors"
    )
    process_result: str = dspy.OutputField(
        desc=(
            "Message that summarizes the result of the adversary emulation operation, "
            "including how CTI information influenced the planning and execution."
        )
    )


# Factory function to create tool functions with proper closure
def create_tool_function(session, tool_name, tool_description):
    async def tool_function(**kwargs):
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


# async def run(adversary_emulation_task: str):
#     async with stdio_client(server_params) as (read, write):

#         async with ClientSession(read, write) as session:
#             # Initialize the connection
#             await session.initialize()
#             # List available tools
#             tools = await session.list_tools()

#             # Convert MCP tools to DSPy tools
#             dspy_tools = []
#             for tool in tools.tools:
#                 dspy_tools.append(dspy.Tool.from_mcp_tool(session, tool))

#             react = dspy.ReAct(DSPyCalderaPlannerClient, tools=dspy_tools)
#             result = await react.acall(
#                 adversary_emulation_task=adversary_emulation_task
#             )
#             print(json.dumps(result.toDict(), indent=4))
async def run(adversary_emulation_task: str, rag_context=None):
    # Ensure LLM is configured
    if not dspy.settings.lm:
        llm_config = get_llm_config()
        configure_llm(llm_config)
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()

            dspy_tools = [
                dspy.Tool.from_mcp_tool(session, tool)
                for tool in tools.tools
            ]

            # Choose signature based on whether RAG context is available
            if rag_context:
                signature = DSPyCalderaPlannerClientWithRAG
                formatted_context = format_rag_context(rag_context)
                react = dspy.ReAct(signature, tools=dspy_tools)
                result = await react.acall(
                    adversary_emulation_task=adversary_emulation_task,
                    cti_context=formatted_context
                )
            else:
                signature = DSPyCalderaPlannerClient
                react = dspy.ReAct(signature, tools=dspy_tools)
                result = await react.acall(
                    adversary_emulation_task=adversary_emulation_task
                )
            
            return result


# if __name__ == "__main__":
#     import asyncio

#     asyncio.run(
#         run(
#             "Find some abilities that constitutes a stealer adversary which includes credential-access and exfiltration, then create an adversary with those abilities, then create an operation with the adversary"
#         )
#     )
