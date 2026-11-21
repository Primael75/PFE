import pytest
from fastapi.testclient import TestClient
from fastmcp import Client

from agritech.example import api, mcp_server
from agritech.example.prices import get_demo_price

KNOWN = {"market": "Market A", "crop": "maize"}
UNKNOWN = {"market": "Market Z", "crop": "maize"}


def test_domain_finds_a_known_price():
    assert get_demo_price(**KNOWN).value == 250.0


def test_domain_returns_none_for_missing_data():
    assert get_demo_price(**UNKNOWN) is None


@pytest.mark.anyio
async def test_case_a_tool_returns_the_price():
    async with Client(mcp_server.mcp) as client:
        result = await client.call_tool("demo_price", KNOWN)
    assert result.structured_content["value"] == 250.0


@pytest.mark.anyio
async def test_case_a_tool_reports_missing_data():
    async with Client(mcp_server.mcp) as client:
        result = await client.call_tool("demo_price", UNKNOWN, raise_on_error=False)
    assert result.is_error


def test_case_b_route_returns_the_price():
    response = TestClient(api.api).get("/prices/Market%20A/maize")
    assert response.status_code == 200
    assert response.json()["value"] == 250.0


def test_case_b_route_reports_missing_data():
    response = TestClient(api.api).get("/prices/Market%20Z/maize")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_case_b_exposes_only_the_tagged_route():
    async with Client(api.mcp) as client:
        tools = await client.list_tools()
    assert [tool.name for tool in tools] == ["demo_price_api"]
