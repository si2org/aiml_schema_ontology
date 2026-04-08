#!/usr/bin/env python3
"""
MCP Server for Monolithic EDA Ontology

This server provides a Model Context Protocol (MCP) interface for exploring
and validating the monolithic EDA ontology (eda-ontology.ttl).

Features:
- SPARQL query execution
- Ontology validation
- Schema exploration
- Graph statistics
- Full-text search
"""

import os
import sys
import argparse
import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Dict, List, Tuple, Set, Any

import rdflib
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, Literal

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base

# Configure logging
logger = logging.getLogger(__name__)

if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)]
    )

logger.info(f"Python path: {sys.executable}")
logger.info(f"PATH: {os.environ.get('PATH', 'UNSET')}")

# Check for SPARQLStore availability
try:
    from rdflib.plugins.stores.sparqlstore import SPARQLStore
    HAS_SPARQLSTORE = True
except ImportError:
    HAS_SPARQLSTORE = False
    logger.warning("SPARQLStore not available.")

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Monolithic EDA Ontology MCP Server v1.0.0")
parser.add_argument("--file", default="../../ontology/eda_ontology.ttl", help="Path to the ontology file")
parser.add_argument("--adapter", default="../../ontology/eda-ontology-adapter.ttl", help="Path to the adapter ontology")
parser.add_argument("--sparql-endpoint", default="", help="SPARQL endpoint URL (empty for Local File Mode)")
args = parser.parse_args()

logger.info("Starting Monolithic EDA Ontology MCP Server v1.0.0")

# Define MCP instance
mcp = FastMCP(
    "EDA Ontology Explorer (Monolithic)",
    dependencies=["rdflib[sparql]", "requests"],
    lifespan=lambda mcp: triplestore_lifespan(mcp, args.file, args.adapter, args.sparql_endpoint)
)


@asynccontextmanager
async def triplestore_lifespan(
    server: FastMCP,
    ontology_file: str,
    adapter_file: str,
    sparql_endpoint: str
) -> AsyncIterator[Dict[str, Any]]:
    """
    Manage the lifespan of the triplestore.

    Loads the monolithic EDA ontology and optional adapter.
    """
    logger.info(f"Initializing triplestore with ontology_file={ontology_file}")

    metrics = {"queries": 0, "total_time": 0.0}
    max_tokens = 10000

    if sparql_endpoint and HAS_SPARQLSTORE:
        logger.info(f"Connecting to SPARQL endpoint: {sparql_endpoint}")
        try:
            graph = SPARQLStore(query_endpoint=sparql_endpoint)
            graph.query("SELECT ?s WHERE { ?s ?p ?o } LIMIT 1")
            logger.info(f"Successfully connected to {sparql_endpoint}")
        except Exception as e:
            logger.error(f"Failed to connect to SPARQL endpoint: {str(e)}")
            raise
    else:
        graph = rdflib.Graph()

        # Load main ontology
        file_path = os.path.join(os.path.dirname(__file__), ontology_file)
        logger.info(f"Loading ontology: {file_path}")

        try:
            graph.parse(file_path, format="turtle")
            logger.info(f"Loaded {len(graph)} triples from main ontology")
        except FileNotFoundError:
            logger.error(f"Ontology file not found: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to load ontology: {str(e)}")
            raise

        # Load adapter ontology if exists
        adapter_path = os.path.join(os.path.dirname(__file__), adapter_file)
        if os.path.exists(adapter_path):
            try:
                graph.parse(adapter_path, format="turtle")
                logger.info(f"Loaded adapter ontology: {adapter_path}")
            except Exception as e:
                logger.warning(f"Failed to load adapter ontology: {str(e)}")

    try:
        logger.info("Triplestore initialized successfully")
        yield {
            "graph": graph,
            "metrics": metrics,
            "max_tokens": max_tokens,
            "ontology_file": ontology_file,
            "sparql_endpoint": sparql_endpoint
        }
    finally:
        logger.info("Shutting down triplestore connection")


# ============================================================================
# RESOURCES
# ============================================================================

@mcp.resource("graph://main")
def get_graph() -> str:
    """Retrieve the main graph serialized in Turtle format."""
    logger.debug("Fetching main graph")
    graph = mcp._lifespan_context["graph"]
    try:
        if HAS_SPARQLSTORE and isinstance(graph, SPARQLStore):
            results = graph.query("SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 100")
            temp_graph = rdflib.Graph()
            for s, p, o in results:
                temp_graph.add((s, p, o))
            return temp_graph.serialize(format="turtle")
        return graph.serialize(format="turtle")
    except Exception as e:
        logger.error(f"Error serializing graph: {str(e)}")
        raise


@mcp.resource("schema://classes")
def get_classes() -> str:
    """Retrieve all OWL classes from the ontology."""
    graph = mcp._lifespan_context["graph"]
    query = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT DISTINCT ?class ?label ?comment WHERE {
        ?class a owl:Class .
        OPTIONAL { ?class rdfs:label ?label }
        OPTIONAL { ?class rdfs:comment ?comment }
    }
    ORDER BY ?class
    """
    try:
        results = graph.query(query)
        output = []
        for row in results:
            cls = str(row['class'])
            label = str(row['label']) if row['label'] else ""
            comment = str(row['comment']) if row['comment'] else ""
            output.append(f"{cls}\t{label}\t{comment[:100]}")
        return "\n".join(output)
    except Exception as e:
        logger.error(f"Schema query error: {str(e)}")
        raise


@mcp.resource("schema://properties")
def get_properties() -> str:
    """Retrieve all properties from the ontology."""
    graph = mcp._lifespan_context["graph"]
    query = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT DISTINCT ?prop ?type ?label ?domain ?range WHERE {
        { ?prop a owl:ObjectProperty . BIND("ObjectProperty" as ?type) }
        UNION
        { ?prop a owl:DatatypeProperty . BIND("DatatypeProperty" as ?type) }
        UNION
        { ?prop a owl:AnnotationProperty . BIND("AnnotationProperty" as ?type) }
        OPTIONAL { ?prop rdfs:label ?label }
        OPTIONAL { ?prop rdfs:domain ?domain }
        OPTIONAL { ?prop rdfs:range ?range }
    }
    ORDER BY ?type ?prop
    """
    try:
        results = graph.query(query)
        output = []
        for row in results:
            prop = str(row['prop'])
            ptype = str(row['type'])
            label = str(row['label']) if row['label'] else ""
            domain = str(row['domain']) if row['domain'] else ""
            rng = str(row['range']) if row['range'] else ""
            output.append(f"{ptype}\t{prop}\t{label}\t{domain}\t{rng}")
        return "\n".join(output)
    except Exception as e:
        logger.error(f"Property query error: {str(e)}")
        raise


@mcp.resource("schema://hierarchy/{class_name}")
def get_class_hierarchy(class_name: str) -> str:
    """Retrieve the class hierarchy for a given class."""
    graph = mcp._lifespan_context["graph"]

    # Handle both full URI and short name
    if not class_name.startswith("http"):
        class_uri = f"http://example.org/eda#{class_name}"
    else:
        class_uri = class_name

    query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT DISTINCT ?subclass ?label WHERE {{
        ?subclass rdfs:subClassOf <{class_uri}> .
        OPTIONAL {{ ?subclass rdfs:label ?label }}
    }}
    ORDER BY ?subclass
    """
    try:
        results = graph.query(query)
        output = [f"Subclasses of {class_name}:"]
        for row in results:
            subclass = str(row['subclass']).split('#')[-1]
            label = str(row['label']) if row['label'] else ""
            output.append(f"  - {subclass}: {label}")
        return "\n".join(output)
    except Exception as e:
        logger.error(f"Hierarchy query error: {str(e)}")
        raise


@mcp.resource("explore://domains")
def get_eda_domains() -> str:
    """Get the main EDA domains covered by the ontology."""
    graph = mcp._lifespan_context["graph"]

    domains = {
        "EDAProcess": "Root class for all EDA workflow activities",
        "DesignArtifact": "Root class for all design data objects",
        "Tool": "Root class for EDA software tools",
        "Metric": "Root class for quantifiable measures",
        "PhysicalDesign": "Physical layout and implementation",
        "Verification": "Design verification processes",
        "LogicalSynthesis": "RTL to gate-level conversion",
        "Timing": "Timing analysis and constraints",
        "Power": "Power analysis and optimization",
        "Library": "Cell libraries and characterization",
        "Manufacturing": "Semiconductor manufacturing",
        "SystemDesign": "Multi-chiplet and advanced packaging"
    }

    output = ["EDA Ontology Domains:"]
    for domain, desc in domains.items():
        # Count instances
        query = f"""
        PREFIX eda: <http://example.org/eda#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT (COUNT(?class) as ?count) WHERE {{
            ?class rdfs:subClassOf* eda:{domain} .
            ?class a owl:Class .
        }}
        """
        try:
            results = list(graph.query(query))
            count = int(results[0][0]) if results else 0
            output.append(f"  {domain}: {desc} ({count} subclasses)")
        except:
            output.append(f"  {domain}: {desc}")

    return "\n".join(output)


@mcp.resource("metrics://status")
def get_metrics() -> str:
    """Retrieve server metrics in JSON format."""
    metrics = mcp._lifespan_context["metrics"]
    return json.dumps(metrics, indent=2)


# ============================================================================
# TOOLS
# ============================================================================

@mcp.tool()
def sparql_query(query: str, ctx: Context) -> str:
    """
    Execute a SPARQL query on the EDA ontology.

    Args:
        query: The SPARQL query to execute
        ctx: The FastMCP context object

    Returns:
        Query results as formatted string
    """
    graph = ctx.request_context.lifespan_context["graph"]
    start_time = time.time()

    try:
        logger.debug(f"Executing query: {query[:100]}...")
        results = graph.query(query)
        ctx.request_context.lifespan_context["metrics"]["queries"] += 1
        ctx.request_context.lifespan_context["metrics"]["total_time"] += time.time() - start_time

        # Format results
        output_lines = []
        for row in results:
            row_str = " | ".join(str(val) for val in row)
            output_lines.append(row_str)

        return "\n".join(output_lines) if output_lines else "No results found"
    except Exception as e:
        logger.error(f"SPARQL query error: {str(e)}")
        return f"Query error: {str(e)}"


@mcp.tool()
def graph_stats(ctx: Context) -> str:
    """
    Calculate and return statistics about the EDA ontology.

    Returns comprehensive statistics including triple count,
    class counts, property counts, and hierarchy metrics.
    """
    graph = ctx.request_context.lifespan_context["graph"]

    try:
        # Basic counts
        stats = {
            "triple_count": len(graph),
            "unique_subjects": len(set(s for s, _, _ in graph)),
            "unique_predicates": len(set(p for _, p, _ in graph)),
            "unique_objects": len(set(o for _, _, o in graph)),
        }

        # Class count
        class_query = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT (COUNT(DISTINCT ?c) as ?count) WHERE { ?c a owl:Class }
        """
        results = list(graph.query(class_query))
        stats["class_count"] = int(results[0][0]) if results else 0

        # Object property count
        obj_prop_query = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT (COUNT(DISTINCT ?p) as ?count) WHERE { ?p a owl:ObjectProperty }
        """
        results = list(graph.query(obj_prop_query))
        stats["object_property_count"] = int(results[0][0]) if results else 0

        # Datatype property count
        data_prop_query = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT (COUNT(DISTINCT ?p) as ?count) WHERE { ?p a owl:DatatypeProperty }
        """
        results = list(graph.query(data_prop_query))
        stats["datatype_property_count"] = int(results[0][0]) if results else 0

        # Restriction count
        restriction_query = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT (COUNT(?r) as ?count) WHERE { ?r a owl:Restriction }
        """
        results = list(graph.query(restriction_query))
        stats["restriction_count"] = int(results[0][0]) if results else 0

        # Disjoint axiom count
        disjoint_query = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT (COUNT(*) as ?count) WHERE { ?a owl:disjointWith ?b }
        """
        results = list(graph.query(disjoint_query))
        stats["disjoint_axiom_count"] = int(results[0][0]) if results else 0

        return json.dumps(stats, indent=2)
    except Exception as e:
        logger.error(f"Graph stats error: {str(e)}")
        raise


@mcp.tool()
def count_triples(ctx: Context) -> str:
    """Count the total number of triples in the ontology."""
    graph = ctx.request_context.lifespan_context["graph"]
    try:
        return str(len(graph))
    except Exception as e:
        return f"Error counting triples: {str(e)}"


@mcp.tool()
def full_text_search(search_term: str, ctx: Context) -> str:
    """
    Search for entities containing the given term in labels or comments.

    Args:
        search_term: The term to search for (case-insensitive)
        ctx: The FastMCP context object

    Returns:
        Matching entities with their labels and types
    """
    graph = ctx.request_context.lifespan_context["graph"]
    query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT DISTINCT ?entity ?label ?type WHERE {{
        ?entity ?p ?o .
        FILTER(
            REGEX(STR(?entity), "{search_term}", "i") ||
            REGEX(STR(?o), "{search_term}", "i")
        )
        OPTIONAL {{ ?entity rdfs:label ?label }}
        OPTIONAL {{ ?entity a ?type }}
    }}
    LIMIT 50
    """
    try:
        results = graph.query(query)
        output = []
        for row in results:
            entity = str(row['entity']).split('#')[-1] if row['entity'] else ""
            label = str(row['label']) if row['label'] else ""
            etype = str(row['type']).split('#')[-1] if row['type'] else ""
            output.append(f"{entity} ({etype}): {label}")
        return "\n".join(output) if output else f"No results for '{search_term}'"
    except Exception as e:
        logger.error(f"Full-text search error: {str(e)}")
        return f"Error: {str(e)}"


@mcp.tool()
def get_class_info(class_name: str, ctx: Context) -> str:
    """
    Get detailed information about a specific class.

    Args:
        class_name: The class name (e.g., 'TimingPath' or full URI)
        ctx: The FastMCP context object

    Returns:
        Detailed class information including superclasses, properties, etc.
    """
    graph = ctx.request_context.lifespan_context["graph"]

    # Handle both full URI and short name
    if not class_name.startswith("http"):
        class_uri = f"http://example.org/eda#{class_name}"
    else:
        class_uri = class_name

    output = [f"Class: {class_name}"]
    output.append("=" * 50)

    # Get label and comment
    info_query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?label ?comment WHERE {{
        <{class_uri}> rdfs:label ?label .
        OPTIONAL {{ <{class_uri}> rdfs:comment ?comment }}
    }}
    """
    results = list(graph.query(info_query))
    if results:
        output.append(f"Label: {results[0]['label']}")
        if results[0]['comment']:
            output.append(f"Comment: {results[0]['comment']}")

    # Get superclasses
    super_query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?parent WHERE {{
        <{class_uri}> rdfs:subClassOf ?parent .
        FILTER(isURI(?parent))
    }}
    """
    results = list(graph.query(super_query))
    if results:
        output.append("\nSuperclasses:")
        for row in results:
            parent = str(row['parent']).split('#')[-1]
            output.append(f"  - {parent}")

    # Get subclasses
    sub_query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?child WHERE {{
        ?child rdfs:subClassOf <{class_uri}> .
        FILTER(isURI(?child))
    }}
    """
    results = list(graph.query(sub_query))
    if results:
        output.append("\nSubclasses:")
        for row in results:
            child = str(row['child']).split('#')[-1]
            output.append(f"  - {child}")

    # Get properties with this class as domain
    prop_query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?prop ?range WHERE {{
        ?prop rdfs:domain <{class_uri}> .
        OPTIONAL {{ ?prop rdfs:range ?range }}
    }}
    """
    results = list(graph.query(prop_query))
    if results:
        output.append("\nProperties (as domain):")
        for row in results:
            prop = str(row['prop']).split('#')[-1]
            rng = str(row['range']).split('#')[-1] if row['range'] else "?"
            output.append(f"  - {prop} -> {rng}")

    # Get disjoint classes
    disjoint_query = f"""
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT ?disjoint WHERE {{
        {{ <{class_uri}> owl:disjointWith ?disjoint }}
        UNION
        {{ ?disjoint owl:disjointWith <{class_uri}> }}
    }}
    """
    results = list(graph.query(disjoint_query))
    if results:
        output.append("\nDisjoint with:")
        for row in results:
            disjoint = str(row['disjoint']).split('#')[-1]
            output.append(f"  - {disjoint}")

    return "\n".join(output)


@mcp.tool()
def health_check(ctx: Context) -> str:
    """Check the health of the triplestore connection."""
    graph = ctx.request_context.lifespan_context["graph"]
    try:
        graph.query("SELECT ?s WHERE { ?s ?p ?o } LIMIT 1")
        return "Healthy"
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return f"Unhealthy: {str(e)}"


@mcp.tool()
def get_mode(ctx: Context) -> str:
    """Get the current mode of the server."""
    ontology_file = ctx.request_context.lifespan_context["ontology_file"]
    sparql_endpoint = ctx.request_context.lifespan_context["sparql_endpoint"]
    if sparql_endpoint:
        return f"SPARQL Endpoint Mode: {sparql_endpoint}"
    else:
        return f"Local File Mode: {ontology_file}"


@mcp.tool()
def set_max_tokens(tokens: int, ctx: Context) -> str:
    """Set the maximum token limit for prompts."""
    if tokens <= 0:
        return "Error: tokens must be positive."
    ctx.request_context.lifespan_context["max_tokens"] = tokens
    logger.info(f"Set max_tokens to {tokens}")
    return f"max_tokens set to {tokens}"


# ============================================================================
# VALIDATION TOOL
# ============================================================================

class OntologyValidator:
    """Comprehensive ontology validation."""

    def __init__(self):
        self.graph = Graph()
        self.validation_results = {
            'syntax_valid': False,
            'owl_profile_violations': [],
            'inconsistencies': [],
            'warnings': [],
            'statistics': {},
            'namespaces': {},
            'classes': [],
            'properties': []
        }

    def read_turtle(self, file_path: str) -> bool:
        """Parse Turtle file."""
        try:
            logger.info(f"Reading Turtle file: {file_path}")
            self.graph.parse(file_path, format="turtle")
            self.validation_results['syntax_valid'] = True
            logger.info(f"Successfully parsed {len(self.graph)} triples")
            return True
        except Exception as e:
            logger.error(f"Syntax error in Turtle file: {e}")
            self.validation_results['syntax_valid'] = False
            self.validation_results['inconsistencies'].append(f"Syntax error: {e}")
            return False

    def extract_namespaces(self):
        """Extract all namespaces."""
        namespaces = {}
        for prefix, namespace in self.graph.namespaces():
            namespaces[str(prefix)] = str(namespace)
        self.validation_results['namespaces'] = namespaces

    def analyze_ontology_structure(self):
        """Analyze structural components."""
        # Find classes
        classes = list(self.graph.subjects(RDF.type, OWL.Class))
        classes.extend(list(self.graph.subjects(RDF.type, RDFS.Class)))
        self.validation_results['classes'] = [str(cls) for cls in set(classes) if isinstance(cls, URIRef)]

        # Find properties
        object_props = list(self.graph.subjects(RDF.type, OWL.ObjectProperty))
        data_props = list(self.graph.subjects(RDF.type, OWL.DatatypeProperty))
        all_properties = object_props + data_props
        self.validation_results['properties'] = [str(prop) for prop in set(all_properties) if isinstance(prop, URIRef)]

    def calculate_statistics(self):
        """Calculate ontology statistics."""
        stats = {
            'total_triples': len(self.graph),
            'unique_subjects': len(set(self.graph.subjects())),
            'unique_predicates': len(set(self.graph.predicates())),
            'unique_objects': len(set(self.graph.objects())),
            'class_count': len(self.validation_results['classes']),
            'object_property_count': len([p for p in self.validation_results['properties']
                                        if (URIRef(p), RDF.type, OWL.ObjectProperty) in self.graph]),
            'datatype_property_count': len([p for p in self.validation_results['properties']
                                          if (URIRef(p), RDF.type, OWL.DatatypeProperty) in self.graph])
        }

        # Restriction count
        restrictions = list(self.graph.subjects(RDF.type, OWL.Restriction))
        stats['restriction_count'] = len(restrictions)

        # Disjoint axiom count
        disjoint = list(self.graph.triples((None, OWL.disjointWith, None)))
        stats['disjoint_axiom_count'] = len(disjoint)

        self.validation_results['statistics'] = stats

    def validate_owl_constraints(self):
        """Validate OWL-specific constraints."""
        violations = []
        warnings = []

        # Check for circular subclass relationships
        for cls in [URIRef(c) for c in self.validation_results['classes']]:
            visited = set()
            current = cls
            while current:
                if current in visited:
                    violations.append(f"Circular subclass: {cls}")
                    break
                visited.add(current)
                parents = [p for p in self.graph.objects(current, RDFS.subClassOf) if isinstance(p, URIRef)]
                current = parents[0] if parents else None

        # Check for disjoint class violations
        for s, p, o in self.graph.triples((None, OWL.disjointWith, None)):
            if isinstance(s, URIRef) and isinstance(o, URIRef):
                instances_s = set(self.graph.subjects(RDF.type, s))
                instances_o = set(self.graph.subjects(RDF.type, o))
                common = instances_s & instances_o
                if common:
                    violations.append(f"Disjoint violation: {s} and {o} share instances")

        self.validation_results['owl_profile_violations'] = violations
        self.validation_results['warnings'] = warnings

    def generate_report(self) -> str:
        """Generate validation report."""
        report = []
        report.append("=" * 60)
        report.append("ONTOLOGY VALIDATION REPORT")
        report.append("=" * 60)

        # Syntax
        report.append(f"\n1. SYNTAX VALIDATION")
        report.append(f"   Status: {'PASSED' if self.validation_results['syntax_valid'] else 'FAILED'}")

        # Statistics
        stats = self.validation_results['statistics']
        report.append(f"\n2. ONTOLOGY STATISTICS")
        report.append(f"   Total triples: {stats.get('total_triples', 0)}")
        report.append(f"   Classes: {stats.get('class_count', 0)}")
        report.append(f"   Object properties: {stats.get('object_property_count', 0)}")
        report.append(f"   Datatype properties: {stats.get('datatype_property_count', 0)}")
        report.append(f"   Restrictions: {stats.get('restriction_count', 0)}")
        report.append(f"   Disjoint axioms: {stats.get('disjoint_axiom_count', 0)}")

        # Namespaces
        report.append(f"\n3. NAMESPACES ({len(self.validation_results['namespaces'])})")
        for prefix, uri in list(self.validation_results['namespaces'].items())[:10]:
            report.append(f"   {prefix}: {uri}")

        # Violations
        violations = self.validation_results['owl_profile_violations']
        report.append(f"\n4. OWL VIOLATIONS ({len(violations)})")
        if violations:
            for v in violations[:5]:
                report.append(f"   - {v}")
        else:
            report.append("   No violations found")

        # Warnings
        warnings = self.validation_results['warnings']
        report.append(f"\n5. WARNINGS ({len(warnings)})")
        if warnings:
            for w in warnings[:5]:
                report.append(f"   - {w}")
        else:
            report.append("   No warnings")

        report.append("\n" + "=" * 60)

        return "\n".join(report)

    def validate_ontology(self, file_path: str) -> Dict:
        """Complete validation pipeline."""
        if not self.read_turtle(file_path):
            return self.validation_results

        self.extract_namespaces()
        self.analyze_ontology_structure()
        self.calculate_statistics()
        self.validate_owl_constraints()

        logger.info("Validation complete")
        return self.validation_results


def validate_turtle_file(file_path: str) -> Tuple[bool, str, Dict]:
    """Convenience function to validate a turtle file."""
    validator = OntologyValidator()
    results = validator.validate_ontology(file_path)
    report = validator.generate_report()
    is_valid = results['syntax_valid'] and len(results['inconsistencies']) == 0
    return is_valid, report, results


@mcp.tool()
def validate(ontology_path: str, ctx: Context) -> str:
    """
    Validate an ontology file.

    Args:
        ontology_path: Path to the turtle file to validate
        ctx: The FastMCP context object

    Returns:
        Validation report
    """
    # Handle relative paths
    if not os.path.isabs(ontology_path):
        ontology_path = os.path.join(os.path.dirname(__file__), ontology_path)

    _, report, _ = validate_turtle_file(ontology_path)
    return report


# ============================================================================
# PROMPTS
# ============================================================================

@mcp.prompt()
def analyze_graph_structure(ctx: Context) -> list[base.Message]:
    """Initiate an analysis of the EDA ontology structure."""
    try:
        schema = get_classes()
        return [
            base.UserMessage("Please analyze the structure of the EDA ontology graph."),
            base.UserMessage(f"Here's a sample of classes:\n{schema[:2000]}..."),
            base.AssistantMessage("What specific aspects would you like me to focus on? "
                                "I can analyze class hierarchies, properties, constraints, or specific domains.")
        ]
    except Exception as e:
        logger.error(f"Analyze graph structure error: {str(e)}")
        raise


@mcp.prompt()
def find_relationships(subject: str) -> str:
    """Generate a SPARQL query to find relationships for a given subject."""
    return f"""
    Using the sparql_query tool, find all relationships for <{subject}>:

    SELECT ?predicate ?object WHERE {{
        <http://example.org/eda#{subject}> ?predicate ?object
    }} LIMIT 100
    """


@mcp.prompt()
def tutorial(ctx: Context) -> list[base.Message]:
    """Provide an interactive tutorial for the EDA ontology."""
    return [
        base.UserMessage("Start the EDA Ontology tutorial"),
        base.AssistantMessage(
            "Welcome to the EDA Ontology MCP Server!\n\n"
            "Step 1: Use 'graph_stats' to see ontology statistics.\n"
            "Step 2: Use 'get_class_info' with a class name like 'TimingPath' to learn about classes.\n"
            "Step 3: Use 'full_text_search' to find entities by name.\n"
            "Step 4: Use 'sparql_query' for custom queries.\n\n"
            "What would you like to explore?"
        )
    ]


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting Monolithic EDA Ontology MCP Server")
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        sys.exit(1)
