"""Case A of the template: a native MCP tool, served over streamable HTTP."""

import logging

from fastmcp import FastMCP
from fastmcp.tools import ToolResult

from agritech.core.tool_output import missing_data, to_tool_result
from agritech.example.prices import get_demo_price

logger = logging.getLogger(__name__)

mcp = FastMCP(name="agritech-example")


@mcp.tool
def demo_price(market: str, crop: str) -> ToolResult:
    """Price of a crop on a market, with its source and date (demo data)."""
    logger.info("demo_price called for %s / %s", market, crop)
    result = get_demo_price(market, crop)
    if result is None:
        return missing_data(f"No demo price for {crop} on {market}.")
    return to_tool_result(result)


# Same settings as Fred's Knowledge Flow: no MCP session, JSON responses.
app = mcp.http_app(path="/mcp", stateless_http=True, json_response=True)


if __name__ == "__main__":
    # Logs go to stderr: in stdio, stdout carries the MCP protocol.
    logging.basicConfig(level=logging.INFO)
    mcp.run()  # stdio by default, for local clients such as Claude Desktop
