# Monolithic EDA Ontology - MCP Server and Test Suite

This directory contains the infrastructure for the EDA ontology. 

## Directory Structure

```
usecases/MCP/
├── server.py                      # MCP Server implementation (uses ../../ontology)
├── mcp_client.py                  # MCP Client for testing
├── ontology_validator.py          # Comprehensive validator
├── sparql_queries.py              # SPARQL query catalog
├── mcp.json                       # MCP server configuration
├── makefile                       # Build automation
├── requirements.txt               # Python dependencies (mcp, rdflib, pytest)
├── tests/test_mcp_server.py       # End-to-end server tests (stdio and streamable HTTP)
└── README.md                      # This file
```

## Quick Start from the repository root

The top-level `Makefile` installs, tests and starts the server with absolute paths, so
it works from any client:

```bash
make mcp-install           # create .venv with the ontology + MCP requirements
make test-mcp              # start the server and exercise its tools, resources and prompts
make mcp-server            # stdio server (normally launched by an MCP client)
make mcp-server-http       # streamable HTTP at http://127.0.0.1:8000/mcp (MCP_HOST, MCP_PORT)
make mcp-inspector         # interactive MCP Inspector web UI (needs Node.js)
make mcp-config            # print the `claude mcp add ...` command and an mcp.json snippet
```

`server.py` options: `--file`, `--adapter`, `--sparql-endpoint`, and
`--transport {stdio,streamable-http,sse}` with `--host` / `--port` for HTTP.

**SDK version:** `server.py` uses the MCP Python SDK v1 `FastMCP` API, so
`requirements.txt` pins `mcp<2`. SDK 2.x renamed `FastMCP` to `MCPServer` and changed
other APIs ([migration guide](https://py.sdk.modelcontextprotocol.io/v2/migration/));
porting the server is a separate task. `make test-mcp` fails if an incompatible SDK
is installed.

## Quick Start (this directory)

### Prerequisites

- Python 3.8+
- RDFLib (`pip install rdflib`)
- MCP SDK (`pip install mcp`)
- pytest (`pip install pytest`)

If using micromamba:
```bash
micromamba activate work
```

### Running Tests

```bash
# Run comprehensive test suite
make test

# Quick validation only
make test-quick

# Full tests including pytest
make test-full

# Run pytest directly
make pytest
```

### Starting the MCP Server

```bash
# Using make
make server

# Or directly
python server.py --file ../../ontology/eda_ontology.ttl
```

### Running the Client Demo

```bash
make client
# or
python mcp_client.py
```

## Architecture Overview


### Core Components

#### 1. MCP Server (`server.py`)

The MCP (Model Context Protocol) server provides:

- **SPARQL Query Execution**: Run arbitrary SPARQL queries
- **Graph Statistics**: Triple counts, class counts, property counts
- **Schema Exploration**: List classes, properties, hierarchies
- **Full-Text Search**: Find entities by name patterns
- **Validation**: In-server ontology validation

**Available Tools:**
- `sparql_query(query)`: Execute SPARQL queries
- `graph_stats()`: Get ontology statistics
- `count_triples()`: Count total triples
- `full_text_search(term)`: Search for entities
- `get_class_info(class_name)`: Get class details
- `validate(path)`: Validate an ontology file
- `health_check()`: Check server health

**Available Resources:**
- `graph://main`: Main graph in Turtle format
- `schema://classes`: All OWL classes
- `schema://properties`: All properties
- `schema://hierarchy/{class}`: Class hierarchy
- `explore://domains`: EDA domain overview

#### 2. Ontology Validator (`ontology_validator.py`)

Performs comprehensive validation:

- **Syntax Validation**: Turtle parsing
- **Semantic Validation**: Required classes/properties, hierarchy checks
- **Consistency Checks**: Circular subclasses, disjoint violations
- **Domain Coverage**: EDA-specific domain validation
- **Best Practices**: Labels, comments, documentation

```bash
# Run validation
python ontology_validator.py --path onto --file eda-ontology.ttl

# Generate JSON report
python ontology_validator.py --json > report.json
```

#### 3. SPARQL Query Catalog (`sparql_queries.py`)

Organized collection of reference queries:

- **Core**: Classes, properties, hierarchies
- **Timing**: Timing analysis, clocks, paths
- **Physical**: Placement, routing, CTS
- **Power**: Power domains, UPF
- **DRC**: Design rules, violations
- **System**: Chiplets, interposers
- **And more...**

```bash
# View query catalog
python sparql_queries.py
```

#### 4. Test Suite (`test_eda_ontology.py`)

Pytest-based comprehensive tests:

- Loading and syntax validation
- Class structure verification
- Property requirements
- Domain coverage
- Disjointness axioms
- SPARQL query execution
- Competency questions

```bash
pytest test_eda_ontology.py -v
```

## MCP Configuration

The `mcp.json` file configures the MCP server for integration with LLM clients:

```json
{
    "mcpServers": {
        "EDA_ontology_mono": {
            "command": "micromamba",
            "args": ["run", "-n", "work", "python", "server.py", "--file", "onto/eda-ontology.ttl"],
            "env": {
                "MAMBA_EXE": "/opt/homebrew/bin/micromamba",
                "MAMBA_ROOT_PREFIX": "/Users/ivan/micromamba"
            }
        }
    }
}
```

## Makefile Targets

| Target | Description |
|--------|-------------|
| `make test` | Run comprehensive test suite |
| `make test-quick` | Quick validation only |
| `make test-full` | Full tests including pytest |
| `make pytest` | Run pytest directly |
| `make query-test` | SPARQL query tests only |
| `make validate` | Run ontology validation |
| `make report` | Generate JSON validation report |
| `make server` | Start MCP server |
| `make client` | Run client demo |
| `make queries` | Display query catalog |
| `make stats` | Show ontology statistics |
| `make clean` | Clean generated files |

## Example Usage

### Query Classes
```python
from mcp_client import MCPOntologyClient

client = MCPOntologyClient("onto")
client.initialize("eda-ontology.ttl")

# Get all classes
result = client.query("""
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT ?class WHERE { ?class a owl:Class }
""")
print(f"Found {len(result.data)} classes")
```

### Validate Ontology
```python
from ontology_validator import validate_ontology

is_valid, report_text, report = validate_ontology("onto", "eda-ontology.ttl")
print(report_text)
```

### Run Specific Domain Queries
```python
from sparql_queries import get_queries_by_domain

timing_queries = get_queries_by_domain("timing")
for query in timing_queries:
    result = client.query(query.query)
    print(f"{query.name}: {len(result.data)} results")
```


## References

- [MCP Protocol](https://modelcontextprotocol.io/)
- [RDFLib Documentation](https://rdflib.readthedocs.io/)
- [OWL 2 Web Ontology Language](https://www.w3.org/TR/owl2-overview/)
