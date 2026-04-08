# MCP Server API Reference

This document describes the tools, resources, and prompts available in the Monolithic EDA Ontology MCP Server.

## Quick Start

```bash
# Start the server
python server.py --file ../../ontology/eda_ontology.ttl

# Or via make
make server
```

## Configuration

The server is configured via command-line arguments:

| Argument | Default | Description |
|----------|---------|-------------|
| `--file` | `../../ontology/eda_ontology.ttl` | Path to the main ontology file |
| `--adapter` | `../../ontology/eda-ontology-adapter.ttl` | Path to optional adapter ontology |
| `--sparql-endpoint` | (none) | Remote SPARQL endpoint URL |

---

## Tools

Tools are callable functions that perform actions on the ontology.

### `sparql_query`

Execute a SPARQL query on the EDA ontology.

**Parameters:**
- `query` (string, required): The SPARQL query to execute

**Returns:** Query results as formatted string (pipe-separated values)

**Example:**
```
sparql_query("SELECT ?class WHERE { ?class a owl:Class } LIMIT 10")
```

---

### `graph_stats`

Calculate and return comprehensive statistics about the EDA ontology.

**Parameters:** None

**Returns:** JSON object with statistics

**Example Response:**
```json
{
  "triple_count": 3253,
  "unique_subjects": 892,
  "unique_predicates": 45,
  "unique_objects": 1247,
  "class_count": 261,
  "object_property_count": 114,
  "datatype_property_count": 256,
  "restriction_count": 11,
  "disjoint_axiom_count": 131
}
```

---

### `count_triples`

Count the total number of triples in the ontology.

**Parameters:** None

**Returns:** Integer count as string

---

### `full_text_search`

Search for entities containing the given term in URIs or literal values.

**Parameters:**
- `search_term` (string, required): The term to search for (case-insensitive)

**Returns:** Matching entities with their labels and types

**Example:**
```
full_text_search("Timing")
```

**Example Response:**
```
TimingAnalysis (Class): Timing Analysis
TimingPath (Class): Timing Path
TimingConstraint (Class): Timing Constraint
...
```

---

### `get_class_info`

Get detailed information about a specific class.

**Parameters:**
- `class_name` (string, required): The class name (short name or full URI)

**Returns:** Detailed class information including:
- Label and comment
- Superclasses
- Subclasses
- Properties with this class as domain
- Disjoint classes

**Example:**
```
get_class_info("TimingPath")
```

**Example Response:**
```
Class: TimingPath
==================================================
Label: Timing Path

Superclasses:
  - TimingAnalysis

Subclasses:
  - SetupPath
  - HoldPath

Properties (as domain):
  - hasStartpoint -> Pin
  - hasEndpoint -> Pin
  - slack -> float

Disjoint with:
  - ClockPath
```

---

### `validate`

Validate an ontology file.

**Parameters:**
- `ontology_path` (string, required): Path to the turtle file to validate

**Returns:** Validation report including:
- Syntax validation status
- Statistics
- Namespaces
- Violations and warnings

---

### `health_check`

Check the health of the triplestore connection.

**Parameters:** None

**Returns:** "Healthy" or error message

---

### `get_mode`

Get the current mode of the server.

**Parameters:** None

**Returns:** Current mode (Local File Mode or SPARQL Endpoint Mode) with path/URL

---

### `set_max_tokens`

Set the maximum token limit for prompts.

**Parameters:**
- `tokens` (integer, required): Maximum token count (must be positive)

**Returns:** Confirmation message

---

## Resources

Resources provide read-only access to ontology data.

### `graph://main`

Retrieve the main graph serialized in Turtle format.

**Returns:** Complete ontology in Turtle syntax

---

### `schema://classes`

Retrieve all OWL classes from the ontology.

**Returns:** Tab-separated list of classes with labels and comments
```
URI    Label    Comment
```

---

### `schema://properties`

Retrieve all properties from the ontology.

**Returns:** Tab-separated list of properties organized by type
```
Type    URI    Label    Domain    Range
```

---

### `schema://hierarchy/{class_name}`

Retrieve the class hierarchy for a given class.

**Parameters:**
- `class_name`: The class name (URL parameter)

**Returns:** List of subclasses with labels

**Example:**
```
schema://hierarchy/PhysicalDesign
```

---

### `explore://domains`

Get the main EDA domains covered by the ontology with subclass counts.

**Returns:** Domain descriptions with statistics

**Example Response:**
```
EDA Ontology Domains:
  EDAProcess: Root class for all EDA workflow activities (45 subclasses)
  DesignArtifact: Root class for all design data objects (32 subclasses)
  Tool: Root class for EDA software tools (8 subclasses)
  ...
```

---

### `metrics://status`

Retrieve server metrics in JSON format.

**Returns:** JSON object with query counts and timing

```json
{
  "queries": 42,
  "total_time": 1.234
}
```

---

## Prompts

Prompts provide structured conversation starters.

### `analyze_graph_structure`

Initiate an analysis of the EDA ontology structure.

**Returns:** Multi-message prompt with class sample and analysis options

---

### `find_relationships`

Generate a SPARQL query to find relationships for a given subject.

**Parameters:**
- `subject` (string): The entity to find relationships for

**Returns:** SPARQL query template

---

### `tutorial`

Provide an interactive tutorial for the EDA ontology.

**Returns:** Step-by-step tutorial messages for exploring the ontology

---

## Error Handling

All tools return error messages in a consistent format:

```
Query error: <description>
Error: <description>
```

Common errors:
- **Syntax errors**: Invalid SPARQL syntax
- **Not found**: Class or property doesn't exist
- **Load errors**: Failed to load ontology file

---

## Example Session

```python
# 1. Check server health
health_check()
# -> "Healthy"

# 2. Get statistics
graph_stats()
# -> {"triple_count": 3253, "class_count": 261, ...}

# 3. Search for timing concepts
full_text_search("Timing")
# -> List of timing-related classes

# 4. Get detailed info on a class
get_class_info("TimingPath")
# -> Full class description

# 5. Run custom query
sparql_query("""
    PREFIX eda: <http://example.org/eda#>
    SELECT ?class WHERE {
        ?class rdfs:subClassOf eda:PhysicalDesign
    }
""")
# -> Placement | Routing | CTS | ...
```

---

## Integration with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "eda-ontology": {
      "command": "python",
      "args": ["/path/to/usecases/MCP/server.py", "--file", "../../ontology/eda_ontology.ttl"],
      "cwd": "/path/to/usecases/MCP"
    }
  }
}
```

Or use the provided `mcp.json` configuration with micromamba.
