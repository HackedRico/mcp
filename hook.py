from app.utility.base_world import BaseWorld
from plugins.mcp.app.mcp_gui import McpGUI
from plugins.mcp.app.mcp_api import McpAPI
from plugins.mcp.app.mcp_svc import MCPService

name = 'mcp'
description = 'Attachment for Model Context Protocol'
address = '/plugin/mcp/gui'
access = BaseWorld.Access.APP
# def get_config_path():
#     return 'plugins/mcp/conf/default.yml'


async def enable(services):
    """
    Enable the MCP plugin by registering its services and routes.
    
    :param services: The service registry to add the MCP services to.
    """
    
    app = services.get('app_svc').application
    #  ✅ Register MCPService so it's available in services.get('mcp_svc')
    services.get('data_svc').add_service('mcp_svc', MCPService(services))
    print("[MCP] Enabling MCP plugin...")
    
    mcp_gui = McpGUI(services, name=name, description=description)
    app.router.add_static('/mcp', 'plugins/mcp/static/', append_version=True)
    # app.router.add_route('GET', '/plugin/mcp/gui', mcp_gui.splash)

    mcp_api = McpAPI(services)
    
    # Add API routes here
    app.router.add_route('POST', '/plugin/mcp/execute', mcp_api.execute)


