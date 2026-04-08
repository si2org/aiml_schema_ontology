# Makefile for Monolithic EDA Ontology Testing and Validation

.PHONY: all clean test test-full test-quick validate query-test pytest report help server client

# Extract micromamba executable path from mcp.json
MICROMAMBA_EXE := $(shell grep -oP '"MAMBA_EXE":"\K[^"]+' mcp.json 2>/dev/null || echo "micromamba")
PYTHON_ENV_CMD := $(MICROMAMBA_EXE) run -n work python

# Ontology files
ONTOLOGY_DIR := ../../ontology
MAIN_ONTOLOGY := eda_ontology.ttl
ADAPTER_ONTOLOGY := eda-ontology-adapter.ttl

# Default target
all: test

# Help target
help:
	@echo "=============================================="
	@echo "Monolithic EDA Ontology - Build Targets"
	@echo "=============================================="
	@echo ""
	@echo "Testing:"
	@echo "  make test        - Run comprehensive test suite"
	@echo "  make test-quick  - Run quick validation only"
	@echo "  make test-full   - Run all tests including pytest"
	@echo "  make pytest      - Run pytest test suite directly"
	@echo "  make query-test  - Run SPARQL query tests only"
	@echo ""
	@echo "Validation:"
	@echo "  make validate    - Run ontology validation"
	@echo "  make report      - Generate validation report (JSON)"
	@echo ""
	@echo "Server & Client:"
	@echo "  make server      - Start MCP server"
	@echo "  make client      - Run MCP client demo"
	@echo ""
	@echo "Utilities:"
	@echo "  make queries     - Display SPARQL query catalog"
	@echo "  make stats       - Show ontology statistics"
	@echo "  make clean       - Clean generated files"
	@echo ""

# Comprehensive test suite
test:
	@echo "========================================"
	@echo "Running Monolithic EDA Ontology Tests"
	@echo "========================================"
	$(PYTHON_ENV_CMD) run_tests.py --path $(ONTOLOGY_DIR) --main $(MAIN_ONTOLOGY)

# Quick validation only
test-quick:
	@echo "Running quick validation..."
	$(PYTHON_ENV_CMD) run_tests.py --path $(ONTOLOGY_DIR) --main $(MAIN_ONTOLOGY) --validate-only

# Full test suite including pytest
test-full:
	@echo "Running full test suite..."
	$(PYTHON_ENV_CMD) run_tests.py --path $(ONTOLOGY_DIR) --main $(MAIN_ONTOLOGY) --pytest

# Run ontology validation
validate:
	@echo "Running ontology validation..."
	$(PYTHON_ENV_CMD) ontology_validator.py --path $(ONTOLOGY_DIR) --file $(MAIN_ONTOLOGY)

# Run SPARQL query tests
query-test:
	@echo "Running SPARQL query tests..."
	$(PYTHON_ENV_CMD) run_tests.py --path $(ONTOLOGY_DIR) --main $(MAIN_ONTOLOGY) --query-only

# Run pytest suite
pytest:
	@echo "Running pytest suite..."
	$(PYTHON_ENV_CMD) -m pytest test_eda_ontology.py -v --tb=short

# Run MCP client demo
client:
	@echo "Running MCP client..."
	$(PYTHON_ENV_CMD) mcp_client.py

# Start MCP server
server:
	@echo "Starting MCP server..."
	$(PYTHON_ENV_CMD) server.py --file $(ONTOLOGY_DIR)/$(MAIN_ONTOLOGY)

# Generate validation report as JSON
report:
	@echo "Generating validation report..."
	$(PYTHON_ENV_CMD) ontology_validator.py --path $(ONTOLOGY_DIR) --file $(MAIN_ONTOLOGY) --json > validation_report.json
	@echo "Report saved to validation_report.json"

# Display SPARQL query catalog
queries:
	@echo "SPARQL Query Catalog:"
	$(PYTHON_ENV_CMD) sparql_queries.py

# Show ontology statistics
stats:
	@echo "Ontology Statistics:"
	$(PYTHON_ENV_CMD) -c "from mcp_client import MCPOntologyClient; c = MCPOntologyClient('$(ONTOLOGY_DIR)'); c.initialize('$(MAIN_ONTOLOGY)'); import json; print(json.dumps(c.get_stats(), indent=2))"

# Check ontology file exists
check-ontology:
	@if [ ! -f "$(ONTOLOGY_DIR)/$(MAIN_ONTOLOGY)" ]; then \
		echo "ERROR: Ontology file not found: $(ONTOLOGY_DIR)/$(MAIN_ONTOLOGY)"; \
		exit 1; \
	fi
	@echo "Ontology file exists: $(ONTOLOGY_DIR)/$(MAIN_ONTOLOGY)"

# Clean generated files
clean:
	@echo "Cleaning up generated files..."
	rm -f validation_report.json *.pyc
	rm -rf __pycache__ .pytest_cache
	@echo "Cleanup complete."

# Test with adapter
test-adapter:
	@echo "Running tests with adapter ontology..."
	$(PYTHON_ENV_CMD) run_tests.py --path $(ONTOLOGY_DIR) --main $(MAIN_ONTOLOGY) --adapter $(ADAPTER_ONTOLOGY)

# Validate with adapter
validate-adapter:
	@echo "Validating with adapter ontology..."
	$(PYTHON_ENV_CMD) ontology_validator.py --path $(ONTOLOGY_DIR) --file $(MAIN_ONTOLOGY) --adapter $(ADAPTER_ONTOLOGY)
