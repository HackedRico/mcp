import os
import dspy
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json
import sys
import mlflow

lm = dspy.LM(model="gpt-4o", api_key="")
dspy.configure(lm=lm)

env = os.environ.copy()
venv_site_packages = os.path.join(sys.prefix, "Lib", "site-packages")
if 'PYTHONPATH' in env:
    env['PYTHONPATH'] = f"{venv_site_packages}:{env['PYTHONPATH']}"
else:
    env['PYTHONPATH'] = venv_site_packages


mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("caldera-mcp-client-1")

server_params = StdioServerParameters(
    command="python",
    args=["mcp_server.py"],
    env=env,
)


class DSPyCalderaPlannerClient(dspy.Signature):
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


# Factory function to create tool functions with proper closure
def create_tool_function(session, tool_name, tool_description):
    async def tool_function(**kwargs):
        result = await session.call_tool(tool_name, kwargs)
        return result
    
    tool_function.__doc__ = tool_description
    return tool_function


async def run(adversary_emulation_task: str):
    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            # List available tools
            tools = await session.list_tools()

            # Convert MCP tools to DSPy tools
            dspy_tools = []
            for tool in tools.tools:
                dspy_tools.append(dspy.Tool.from_mcp_tool(session, tool))

            react = dspy.ReAct(DSPyCalderaPlannerClient, tools=dspy_tools)
            result = await react.acall(
                adversary_emulation_task=adversary_emulation_task
            )
            print(json.dumps(result.toDict(), indent=4))


if __name__ == "__main__":
    import asyncio

    asyncio.run(
        run(
            "I want to create a few abilities related to persistence with WMI for windows, then create an adversary with those abilities.  Please create more than one ability."
        )
    )
