# Top-level Makefile for the Si2 AI/ML schema ontology.
#
# Covers the core ontology in ontology/ and the MCP server in usecases/MCP/. The other
# use cases under usecases/ have their own dependencies and instructions.
#
# Python: uses .venv/bin/python when .venv exists (see `make install`), otherwise
# python3 from PATH. Override with `make test PYTHON=/path/to/python`.

VENV        := .venv
PYTHON      ?= $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,python3)

ONTOLOGY_DIR := ontology
MAIN_TTL     := eda_ontology.ttl
ADAPTER_TTL  := eda-ontology-adapter.ttl
TTL_FILES    := $(ONTOLOGY_DIR)/$(MAIN_TTL) $(ONTOLOGY_DIR)/$(ADAPTER_TTL)
TESTS_DIR    := $(ONTOLOGY_DIR)/tests
REQUIREMENTS := $(ONTOLOGY_DIR)/requirements.txt

MCP_DIR          := usecases/MCP
MCP_REQUIREMENTS := $(MCP_DIR)/requirements.txt
MCP_SERVER       := $(CURDIR)/$(MCP_DIR)/server.py
MCP_ARGS         := --file $(CURDIR)/$(ONTOLOGY_DIR)/$(MAIN_TTL) --adapter $(CURDIR)/$(ONTOLOGY_DIR)/$(ADAPTER_TTL)
MCP_HOST         ?= 127.0.0.1
MCP_PORT         ?= 8000
MCP_NAME         ?= eda-ontology
# Absolute interpreter path for MCP client configs (evaluated only when used)
PYTHON_ABS        = $(shell $(PYTHON) -c 'import sys; print(sys.executable)')

.DEFAULT_GOAL := help
.PHONY: help venv install syntax validate reason test test-pytest test-runner \
        test-adapter check check-all stats clean distclean \
        mcp-install test-mcp mcp-server mcp-server-http mcp-inspector mcp-config

help: ## Show this help
	@echo "Si2 AI/ML schema ontology - make targets"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Python in use: $(PYTHON)"

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

$(VENV)/bin/python:
	python3 -m venv $(VENV)

venv: $(VENV)/bin/python ## Create the .venv virtual environment

install: $(VENV)/bin/python ## Create .venv and install ontology/requirements.txt
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install -r $(REQUIREMENTS)

# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

syntax: ## Parse every Turtle file (fast syntax check)
	@$(PYTHON) -c "import sys, rdflib; \
	[print(f'OK  {f}: {len(rdflib.Graph().parse(f, format=\"turtle\"))} triples') for f in sys.argv[1:]]" \
	$(TTL_FILES)

validate: ## Run the structural ontology validator
	$(PYTHON) $(TESTS_DIR)/run_tests.py --path $(ONTOLOGY_DIR) --main $(MAIN_TTL) --validate-only

reason: ## OWL-RL consistency check (needs owlrl)
	$(PYTHON) $(TESTS_DIR)/check_consistency.py $(TTL_FILES)

test-pytest: ## Run the pytest suites
	$(PYTHON) -m pytest $(TESTS_DIR)/test_eda_ontology.py $(TESTS_DIR)/test_process_terminology.py -q

test-runner: ## Run the ontology test runner (integrity, validation, SPARQL catalog)
	$(PYTHON) $(TESTS_DIR)/run_tests.py --path $(ONTOLOGY_DIR) --main $(MAIN_TTL)

test-adapter: ## Run the test runner with the adapter ontology loaded
	$(PYTHON) $(TESTS_DIR)/run_tests.py --path $(ONTOLOGY_DIR) --main $(MAIN_TTL) --adapter $(ADAPTER_TTL)

test: test-pytest test-runner ## Run all ontology tests

check: syntax validate reason test ## Ontology CI: syntax, validate, reason, test

check-all: check test-mcp ## Ontology CI plus the MCP server tests

# ---------------------------------------------------------------------------
# MCP server (usecases/MCP)
# ---------------------------------------------------------------------------

mcp-install: install ## Create .venv with the ontology and MCP server requirements
	$(VENV)/bin/python -m pip install -r $(MCP_REQUIREMENTS)

test-mcp: ## End-to-end MCP tests: start the server, call tools/resources over stdio and HTTP
	@$(PYTHON) -c "import mcp" 2>/dev/null || { echo "mcp SDK not installed: run 'make mcp-install'"; exit 1; }
	$(PYTHON) -m pytest $(MCP_DIR)/tests -q

mcp-server: ## Start the MCP server on stdio (for an MCP client; waits on stdin, Ctrl-C to stop)
	@echo "MCP server on stdio. It is normally launched by an MCP client; see 'make mcp-config'." >&2
	$(PYTHON) $(MCP_SERVER) $(MCP_ARGS)

mcp-server-http: ## Start the MCP server over streamable HTTP at http://MCP_HOST:MCP_PORT/mcp
	$(PYTHON) $(MCP_SERVER) $(MCP_ARGS) --transport streamable-http --host $(MCP_HOST) --port $(MCP_PORT)

mcp-inspector: ## Open the MCP Inspector web UI on the server (needs Node.js / npx)
	@command -v npx >/dev/null || { echo "npx not found: install Node.js"; exit 1; }
	npx -y @modelcontextprotocol/inspector $(PYTHON_ABS) $(MCP_SERVER) $(MCP_ARGS)

mcp-config: ## Print client config (Claude Code command and mcp.json) with absolute paths
	@echo "# Claude Code:"
	@echo "claude mcp add $(MCP_NAME) -- $(PYTHON_ABS) $(MCP_SERVER) $(MCP_ARGS)"
	@echo ""
	@echo "# mcp.json / claude_desktop_config.json:"
	@printf '{\n  "mcpServers": {\n    "%s": {\n      "command": "%s",\n      "args": ["%s", "--file", "%s", "--adapter", "%s"]\n    }\n  }\n}\n' \
		"$(MCP_NAME)" "$(PYTHON_ABS)" "$(MCP_SERVER)" \
		"$(CURDIR)/$(ONTOLOGY_DIR)/$(MAIN_TTL)" "$(CURDIR)/$(ONTOLOGY_DIR)/$(ADAPTER_TTL)"

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

stats: ## Print class/property/triple counts
	@$(PYTHON) -c "import rdflib; from rdflib import RDF, OWL; \
	g = rdflib.Graph().parse('$(ONTOLOGY_DIR)/$(MAIN_TTL)', format='turtle'); \
	n = lambda t: len(set(g.subjects(RDF.type, t))); \
	print(f'triples:             {len(g)}'); \
	print(f'classes:             {n(OWL.Class)}'); \
	print(f'object properties:   {n(OWL.ObjectProperty)}'); \
	print(f'datatype properties: {n(OWL.DatatypeProperty)}'); \
	print(f'deprecated terms:    {len(set(g.subjects(OWL.deprecated, None)))}')"

clean: ## Remove Python caches and generated reports
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	find . -name .pytest_cache -type d -prune -exec rm -rf {} +
	rm -f $(TESTS_DIR)/validation_report.json usecases/MCP/validation_report.json

distclean: clean ## Also remove the .venv virtual environment
	rm -rf $(VENV)
