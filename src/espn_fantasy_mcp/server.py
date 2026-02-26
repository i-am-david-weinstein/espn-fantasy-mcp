"""MCP server implementation for ESPN Fantasy Baseball."""
import json
import logging
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from espn_fantasy_mcp.tools import league_tools, team_tools, player_tools, roster_tools, transaction_tools

logger = logging.getLogger(__name__)
app = Server("espn-fantasy")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Return all available tools."""
    return [
        *league_tools.get_tools(),
        *team_tools.get_tools(),
        *player_tools.get_tools(),
        *roster_tools.get_tools(),
        *transaction_tools.get_tools(),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        # Route to appropriate module based on tool name
        if name in ["get_league_settings", "get_standings"]:
            result = await league_tools.handle_tool(name, arguments)
        elif name in ["get_team", "get_roster"]:
            result = await team_tools.handle_tool(name, arguments)
        elif name in ["get_free_agents", "get_player_info"]:
            result = await player_tools.handle_tool(name, arguments)
        elif name in ["modify_lineup"]:
            result = await roster_tools.handle_tool(name, arguments)
        elif name in ["add_free_agent", "drop_player", "claim_waiver", "cancel_waiver"]:
            result = await transaction_tools.handle_tool(name, arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=result)]

    except Exception as e:
        logger.error(f"Tool call failed: {e}")
        error_response = json.dumps(
            {"success": False, "error": type(e).__name__, "message": str(e)}, indent=2
        )
        return [TextContent(type="text", text=error_response)]


async def main():
    """Run the MCP server."""
    logger.info("Starting ESPN Fantasy MCP server")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
