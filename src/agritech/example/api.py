"""Case B of the template: an API route, also exposed as an MCP tool."""

import logging

from fastapi import FastAPI, HTTPException
from fastmcp import FastMCP
from fastmcp.server.providers.openapi import MCPType, RouteMap

from agritech.core.tool_output import SourcedValue
from agritech.example.prices import get_demo_price

logger = logging.getLogger(__name__)

api = FastAPI(title="agritech-example-api")


@api.get("/prices/{market}/{crop}", tags=["mcp"], operation_id="demo_price_api")
def read_demo_price(market: str, crop: str) -> SourcedValue:
    """Price of a crop on a market, with its source and date (demo data)."""
    logger.info("read_demo_price called for %s / %s", market, crop)
    result = get_demo_price(market, crop)
    if result is None:
        raise HTTPException(
            status_code=404, detail=f"No demo price for {crop} on {market}."
        )
    return result


# Only routes tagged "mcp" become tools; every other route stays API-only.
mcp = FastMCP.from_fastapi(
    app=api,
    route_maps=[
        RouteMap(tags={"mcp"}, mcp_type=MCPType.TOOL),
        RouteMap(mcp_type=MCPType.EXCLUDE),
    ],
)


if __name__ == "__main__":
    # Logs go to stderr: in stdio, stdout carries the MCP protocol.
    logging.basicConfig(level=logging.INFO)
    mcp.run()  # MCP side only, over stdio; the REST API is served by uvicorn
