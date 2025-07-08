from app.utility.base_world import BaseWorld
from plugins.mcp.app.mcp_gui import McpGUI
from plugins.mcp.app.mcp_api import McpAPI

name = 'Mcp'
description = 'Attachment for Model Context Protocol'
address = '/plugin/mcp/gui'
access = BaseWorld.Access.RED


async def enable(services):
    app = services.get('app_svc').application
    mcp_gui = McpGUI(services, name=name, description=description)
    app.router.add_static('/mcp', 'plugins/mcp/static/', append_version=True)
    app.router.add_route('GET', '/plugin/mcp/gui', mcp_gui.splash)

    mcp_api = McpAPI(services)
    # Add API routes here
    app.router.add_route('POST', '/plugin/mcp/mirror', mcp_api.mirror)

