#!/usr/bin/env python3
"""
End-to-end tests for the EDA ontology MCP server (usecases/MCP/server.py).

The server is started as a real subprocess and driven through the official MCP
Python SDK client, exactly as an MCP host (Claude Code, Claude Desktop, an IDE)
would do it: over stdio, and once over the streamable-HTTP transport.

Run:  make test-mcp      (or: pytest usecases/MCP/tests)
"""

import asyncio
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

mcp = pytest.importorskip("mcp")
from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

MCP_DIR = Path(__file__).resolve().parents[1]
SERVER = MCP_DIR / "server.py"
ONTOLOGY = MCP_DIR.parents[1] / "ontology" / "eda_ontology.ttl"
TIMEOUT = 60  # seconds per session; ontology load takes a few seconds

EXPECTED_TOOLS = {
    "sparql_query", "graph_stats", "count_triples", "full_text_search",
    "get_class_info", "health_check", "get_mode", "set_max_tokens", "validate",
}
EXPECTED_RESOURCES = {
    "graph://main", "schema://classes", "schema://properties",
    "explore://domains", "metrics://status",
}
EXPECTED_PROMPTS = {"analyze_graph_structure", "find_relationships", "tutorial"}

ACTIVITY_QUERY = """
PREFIX eda: <http://example.org/eda#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?c WHERE { ?c rdfs:subClassOf eda:Activity }
"""


def _server_params(*extra):
    return StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER), "--file", str(ONTOLOGY), *extra],
        cwd=str(MCP_DIR),
    )


def _text(result):
    """Text of the first content block of a tool result or resource read."""
    if hasattr(result, "contents"):
        return result.contents[0].text
    assert not result.isError, result.content
    return result.content[0].text


async def _exercise(session):
    """Run every request the tests check, in one server session."""
    await session.initialize()
    out = {
        "tools": {t.name for t in (await session.list_tools()).tools},
        "resources": {str(r.uri) for r in (await session.list_resources()).resources},
        "templates": {t.uriTemplate for t in (await session.list_resource_templates()).resourceTemplates},
        "prompts": {p.name for p in (await session.list_prompts()).prompts},
        "call": {},
        "read": {},
    }
    calls = {
        "health_check": {},
        "count_triples": {},
        "graph_stats": {},
        "get_mode": {},
        "get_class_info": {"class_name": "ProcessTechnology"},
        "full_text_search": {"search_term": "Corner"},
        "sparql_query": {"query": ACTIVITY_QUERY},
    }
    for name, arguments in calls.items():
        out["call"][name] = await session.call_tool(name, arguments)
    out["call"]["bad_sparql"] = await session.call_tool("sparql_query", {"query": "SELECT nonsense"})
    for uri in sorted(EXPECTED_RESOURCES) + ["schema://hierarchy/EDAProcess"]:
        out["read"][uri] = await session.read_resource(uri)
    return out


async def _run_stdio(*extra):
    async with stdio_client(_server_params(*extra)) as (read, write):
        async with ClientSession(read, write) as session:
            return await _exercise(session)


@pytest.fixture(scope="module")
def transcript():
    return asyncio.run(asyncio.wait_for(_run_stdio(), TIMEOUT))


# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------

def test_lists_expected_tools(transcript):
    assert EXPECTED_TOOLS <= transcript["tools"]


def test_lists_expected_resources(transcript):
    assert EXPECTED_RESOURCES <= transcript["resources"]
    assert "schema://hierarchy/{class_name}" in transcript["templates"]


def test_lists_expected_prompts(transcript):
    assert EXPECTED_PROMPTS <= transcript["prompts"]


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def test_health_check(transcript):
    assert _text(transcript["call"]["health_check"]) == "Healthy"


def test_ontology_loaded(transcript):
    assert int(_text(transcript["call"]["count_triples"])) > 3000
    assert '"class_count"' in _text(transcript["call"]["graph_stats"])


def test_local_file_mode(transcript):
    assert _text(transcript["call"]["get_mode"]).startswith("Local File Mode")


def test_get_class_info(transcript):
    text = _text(transcript["call"]["get_class_info"])
    assert "Class: ProcessTechnology" in text
    assert "Process Technology" in text


def test_full_text_search(transcript):
    assert "ProcessCorner" in _text(transcript["call"]["full_text_search"])


def test_sparql_query_sees_process_split(transcript):
    text = _text(transcript["call"]["sparql_query"])
    assert "#EDAProcess" in text
    assert "#SemiconductorManufacturingProcess" in text


def test_bad_sparql_reports_error_without_crashing(transcript):
    result = transcript["call"]["bad_sparql"]
    text = result.content[0].text if result.content else ""
    assert result.isError or "error" in text.lower()
    # the session kept working after the bad query: later reads succeeded
    assert transcript["read"]["metrics://status"].contents


# ---------------------------------------------------------------------------
# Resources (each one used to fail: they read a non-existent mcp._lifespan_context)
# ---------------------------------------------------------------------------

def test_graph_resource_is_turtle(transcript):
    assert "@prefix eda:" in _text(transcript["read"]["graph://main"])


def test_classes_resource_lists_named_classes_only(transcript):
    lines = _text(transcript["read"]["schema://classes"]).splitlines()
    assert any(line.startswith("http://example.org/eda#ProcessTechnology\t") for line in lines)
    assert all(line.startswith("http") for line in lines), "blank-node classes leaked"


def test_properties_resource(transcript):
    assert "hasProcessCorner" in _text(transcript["read"]["schema://properties"])


def test_domains_resource(transcript):
    text = _text(transcript["read"]["explore://domains"])
    assert "EDAProcess" in text and "SemiconductorManufacturingProcess" in text


def test_metrics_resource_counts_queries(transcript):
    assert '"queries": ' in _text(transcript["read"]["metrics://status"])
    assert '"queries": 0' not in _text(transcript["read"]["metrics://status"])


def test_hierarchy_template(transcript):
    text = _text(transcript["read"]["schema://hierarchy/EDAProcess"])
    assert "MaskDataPreparation" in text
    assert "Doping" not in text


# ---------------------------------------------------------------------------
# Startup behaviour
# ---------------------------------------------------------------------------

def test_missing_ontology_fails_startup(tmp_path):
    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=[str(SERVER), "--file", str(tmp_path / "missing.ttl")],
            cwd=str(MCP_DIR),
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                await session.call_tool("health_check", {})

    with pytest.raises(BaseException):
        asyncio.run(asyncio.wait_for(run(), TIMEOUT))


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_streamable_http_transport():
    try:  # renamed in newer SDKs; keep working with older ones
        from mcp.client.streamable_http import streamable_http_client as http_client
    except ImportError:
        from mcp.client.streamable_http import streamablehttp_client as http_client

    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, str(SERVER), "--file", str(ONTOLOGY),
         "--transport", "streamable-http", "--port", str(port)],
        cwd=str(MCP_DIR), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
    )
    try:
        deadline = time.time() + TIMEOUT
        while time.time() < deadline:
            if proc.poll() is not None:
                pytest.fail(f"server exited early: {proc.stderr.read()}")
            with socket.socket() as s:
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.2)
        else:
            pytest.fail("server did not start listening in time")

        async def run():
            async with http_client(f"http://127.0.0.1:{port}/mcp") as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    return _text(await session.call_tool("health_check", {}))

        assert asyncio.run(asyncio.wait_for(run(), TIMEOUT)) == "Healthy"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
