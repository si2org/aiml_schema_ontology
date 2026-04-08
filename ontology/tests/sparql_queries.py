#!/usr/bin/env python3
"""
Reference SPARQL Queries for Monolithic EDA Ontology

This module provides a comprehensive collection of SPARQL queries
for exploring, validating, and testing the monolithic EDA ontology.
Each query is documented with its purpose and expected results.
"""

from typing import Dict, List, NamedTuple
from dataclasses import dataclass


@dataclass
class SPARQLQuery:
    """Container for a SPARQL query with metadata"""
    name: str
    description: str
    query: str
    domain: str  # core, timing, power, physical, etc.
    expected_min_results: int = 0
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


# Standard prefixes used in all queries
PREFIXES = """
PREFIX eda: <http://example.org/eda#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX qudt: <http://qudt.org/schema/qudt/>
"""


# ============================================================================
# CORE ONTOLOGY QUERIES
# ============================================================================

CORE_QUERIES = [
    SPARQLQuery(
        name="all_owl_classes",
        description="Get all OWL classes defined in the ontology",
        domain="core",
        expected_min_results=50,
        tags=["schema", "classes"],
        query=PREFIXES + """
SELECT DISTINCT ?class ?label ?comment WHERE {
    ?class a owl:Class .
    OPTIONAL { ?class rdfs:label ?label }
    OPTIONAL { ?class rdfs:comment ?comment }
}
ORDER BY ?class
"""
    ),

    SPARQLQuery(
        name="top_level_classes",
        description="Get top-level EDA classes (EDAProcess, DesignArtifact, Tool, Metric)",
        domain="core",
        expected_min_results=4,
        tags=["schema", "hierarchy"],
        query=PREFIXES + """
SELECT ?class ?label WHERE {
    ?class a owl:Class .
    FILTER(?class IN (eda:EDAProcess, eda:DesignArtifact, eda:Tool, eda:Metric))
    OPTIONAL { ?class rdfs:label ?label }
}
"""
    ),

    SPARQLQuery(
        name="eda_process_hierarchy",
        description="Get the complete EDAProcess class hierarchy",
        domain="core",
        expected_min_results=5,
        tags=["hierarchy", "process"],
        query=PREFIXES + """
SELECT ?class ?parent ?label WHERE {
    ?class rdfs:subClassOf* eda:EDAProcess .
    ?class rdfs:subClassOf ?parent .
    FILTER(isURI(?parent))
    OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?parent ?class
"""
    ),

    SPARQLQuery(
        name="design_artifact_hierarchy",
        description="Get all DesignArtifact subclasses",
        domain="core",
        expected_min_results=3,
        tags=["hierarchy", "artifact"],
        query=PREFIXES + """
SELECT ?class ?label WHERE {
    ?class rdfs:subClassOf eda:DesignArtifact .
    OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?class
"""
    ),

    SPARQLQuery(
        name="all_object_properties",
        description="Get all object properties with domain and range",
        domain="core",
        expected_min_results=10,
        tags=["schema", "properties"],
        query=PREFIXES + """
SELECT ?prop ?label ?domain ?range WHERE {
    ?prop a owl:ObjectProperty .
    OPTIONAL { ?prop rdfs:label ?label }
    OPTIONAL { ?prop rdfs:domain ?domain }
    OPTIONAL { ?prop rdfs:range ?range }
}
ORDER BY ?prop
"""
    ),

    SPARQLQuery(
        name="all_datatype_properties",
        description="Get all datatype properties with domain and range",
        domain="core",
        expected_min_results=5,
        tags=["schema", "properties"],
        query=PREFIXES + """
SELECT ?prop ?label ?domain ?range WHERE {
    ?prop a owl:DatatypeProperty .
    OPTIONAL { ?prop rdfs:label ?label }
    OPTIONAL { ?prop rdfs:domain ?domain }
    OPTIONAL { ?prop rdfs:range ?range }
}
ORDER BY ?prop
"""
    ),

    SPARQLQuery(
        name="inverse_properties",
        description="Get all inverse property relationships",
        domain="core",
        expected_min_results=3,
        tags=["schema", "properties"],
        query=PREFIXES + """
SELECT ?prop ?inverse WHERE {
    ?prop owl:inverseOf ?inverse .
}
ORDER BY ?prop
"""
    ),

    SPARQLQuery(
        name="flow_related_classes",
        description="Get all flow and stage related classes",
        domain="core",
        expected_min_results=2,
        tags=["flow", "stage"],
        query=PREFIXES + """
SELECT ?class ?label WHERE {
    {
        ?class a owl:Class .
        FILTER(CONTAINS(STR(?class), "Flow") || CONTAINS(STR(?class), "Stage"))
    }
    OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?class
"""
    ),

    SPARQLQuery(
        name="design_structure_classes",
        description="Get design structure classes (Instance, Net, Pin, Port)",
        domain="core",
        expected_min_results=4,
        tags=["design", "structure"],
        query=PREFIXES + """
SELECT ?class ?label WHERE {
    ?class a owl:Class .
    FILTER(?class IN (eda:Instance, eda:Net, eda:Pin, eda:Port, eda:Design, eda:Netlist))
    OPTIONAL { ?class rdfs:label ?label }
}
"""
    ),
]


# ============================================================================
# TIMING DOMAIN QUERIES
# ============================================================================

TIMING_QUERIES = [
    SPARQLQuery(
        name="timing_classes",
        description="Get all timing-related classes",
        domain="timing",
        expected_min_results=10,
        tags=["timing", "classes"],
        query=PREFIXES + """
SELECT DISTINCT ?class ?label WHERE {
    ?class a owl:Class .
    FILTER(
        CONTAINS(STR(?class), "Timing") ||
        CONTAINS(STR(?class), "Clock") ||
        CONTAINS(STR(?class), "Delay") ||
        CONTAINS(STR(?class), "Path") ||
        CONTAINS(STR(?class), "Slack") ||
        CONTAINS(STR(?class), "Corner") ||
        CONTAINS(STR(?class), "SDC")
    )
    OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?class
"""
    ),

    SPARQLQuery(
        name="timing_analysis_subclasses",
        description="Get subclasses of TimingAnalysis",
        domain="timing",
        expected_min_results=1,
        tags=["timing", "hierarchy"],
        query=PREFIXES + """
SELECT ?class ?label WHERE {
    ?class rdfs:subClassOf eda:TimingAnalysis .
    OPTIONAL { ?class rdfs:label ?label }
}
"""
    ),

    SPARQLQuery(
        name="timing_properties",
        description="Get properties with timing-related domains",
        domain="timing",
        expected_min_results=3,
        tags=["timing", "properties"],
        query=PREFIXES + """
SELECT ?prop ?domain ?range WHERE {
    ?prop a owl:ObjectProperty .
    ?prop rdfs:domain ?domain .
    FILTER(
        CONTAINS(STR(?domain), "Timing") ||
        CONTAINS(STR(?domain), "Clock") ||
        CONTAINS(STR(?domain), "Path")
    )
    OPTIONAL { ?prop rdfs:range ?range }
}
"""
    ),

    SPARQLQuery(
        name="clock_hierarchy",
        description="Get clock-related class hierarchy",
        domain="timing",
        expected_min_results=2,
        tags=["timing", "clock"],
        query=PREFIXES + """
SELECT ?class ?parent WHERE {
    ?class a owl:Class .
    ?class rdfs:subClassOf ?parent .
    FILTER(CONTAINS(STR(?class), "Clock") || CONTAINS(STR(?parent), "Clock"))
    FILTER(isURI(?parent))
}
"""
    ),

    SPARQLQuery(
        name="timing_path_properties",
        description="Get properties related to timing paths",
        domain="timing",
        expected_min_results=1,
        tags=["timing", "path"],
        query=PREFIXES + """
SELECT ?prop ?label ?domain ?range WHERE {
    ?prop a owl:ObjectProperty .
    FILTER(CONTAINS(STR(?prop), "Path") || CONTAINS(STR(?prop), "path"))
    OPTIONAL { ?prop rdfs:label ?label }
    OPTIONAL { ?prop rdfs:domain ?domain }
    OPTIONAL { ?prop rdfs:range ?range }
}
"""
    ),
]


# ============================================================================
# PHYSICAL DESIGN QUERIES
# ============================================================================

PHYSICAL_QUERIES = [
    SPARQLQuery(
        name="physical_design_subclasses",
        description="Get all subclasses of PhysicalDesign",
        domain="physical",
        expected_min_results=4,
        tags=["physical", "hierarchy"],
        query=PREFIXES + """
SELECT ?class ?label WHERE {
    ?class rdfs:subClassOf eda:PhysicalDesign .
    OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?class
"""
    ),

    SPARQLQuery(
        name="placement_disjoint",
        description="Get classes disjoint with Placement",
        domain="physical",
        expected_min_results=3,
        tags=["physical", "disjoint"],
        query=PREFIXES + """
SELECT DISTINCT ?class WHERE {
    { eda:Placement owl:disjointWith ?class }
    UNION
    { ?class owl:disjointWith eda:Placement }
}
"""
    ),

    SPARQLQuery(
        name="routing_classes",
        description="Get routing-related classes",
        domain="physical",
        expected_min_results=1,
        tags=["physical", "routing"],
        query=PREFIXES + """
SELECT ?class ?label WHERE {
    ?class a owl:Class .
    FILTER(CONTAINS(STR(?class), "Routing") || CONTAINS(STR(?class), "Route"))
    OPTIONAL { ?class rdfs:label ?label }
}
"""
    ),

    SPARQLQuery(
        name="cts_classes",
        description="Get Clock Tree Synthesis related classes",
        domain="physical",
        expected_min_results=1,
        tags=["physical", "cts"],
        query=PREFIXES + """
SELECT ?class ?label WHERE {
    ?class a owl:Class .
    FILTER(
        CONTAINS(STR(?class), "CTS") ||
        CONTAINS(STR(?class), "ClockTree") ||
        CONTAINS(STR(?class), "ClockTreeSynthesis")
    )
    OPTIONAL { ?class rdfs:label ?label }
}
"""
    ),

    SPARQLQuery(
        name="floorplan_classes",
        description="Get floorplanning related classes",
        domain="physical",
        expected_min_results=1,
        tags=["physical", "floorplan"],
        query=PREFIXES + """
SELECT ?class ?label WHERE {
    ?class a owl:Class .
    FILTER(CONTAINS(STR(?class), "Floorplan"))
    OPTIONAL { ?class rdfs:label ?label }
}
"""
    ),

    SPARQLQuery(
        name="parasitic_classes",
        description="Get parasitic extraction related classes",
        domain="physical",
        expected_min_results=1,
        tags=["physical", "parasitic"],
        query=PREFIXES + """
SELECT ?class ?label WHERE {
    ?class a owl:Class .
    FILTER(CONTAINS(STR(?class), "Parasitic"))
    OPTIONAL { ?class rdfs:label ?label }
}
"""
    ),
]


# ============================================================================
# POWER DOMAIN QUERIES
# ============================================================================

POWER_QUERIES = [
    SPARQLQuery(
        name="power_classes",
        description="Get all power-related classes",
        domain="power",
        expected_min_results=3,
        tags=["power", "classes"],
        query=PREFIXES + """
SELECT DISTINCT ?class ?label WHERE {
    ?class a owl:Class .
    FILTER(
        CONTAINS(STR(?class), "Power") ||
        CONTAINS(STR(?class), "Voltage") ||
        CONTAINS(STR(?class), "UPF") ||
        CONTAINS(STR(?class), "Energy")
    )
    OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?class
"""
    ),

    SPARQLQuery(
        name="power_metric_subclasses",
        description="Get subclasses of PowerMetric (if any)",
        domain="power",
        expected_min_results=0,
        tags=["power", "metric"],
        query=PREFIXES + """
SELECT ?class ?label WHERE {
    ?class rdfs:subClassOf eda:PowerMetric .
    OPTIONAL { ?class rdfs:label ?label }
}
"""
    ),

    SPARQLQuery(
        name="power_properties",
        description="Get properties with power-related domains or ranges",
        domain="power",
        expected_min_results=1,
        tags=["power", "properties"],
        query=PREFIXES + """
SELECT ?prop ?domain ?range WHERE {
    ?prop a owl:ObjectProperty .
    {
        ?prop rdfs:domain ?domain .
        FILTER(CONTAINS(STR(?domain), "Power"))
    } UNION {
        ?prop rdfs:range ?range .
        FILTER(CONTAINS(STR(?range), "Power"))
    }
}
"""
    ),
]


# ============================================================================
# DRC DOMAIN QUERIES
# ============================================================================

DRC_QUERIES = [
    SPARQLQuery(
        name="drc_classes",
        description="Get all DRC-related classes",
        domain="drc",
        expected_min_results=2,
        tags=["drc", "classes"],
        query=PREFIXES + """
SELECT DISTINCT ?class ?label WHERE {
    ?class a owl:Class .
    FILTER(
        CONTAINS(STR(?class), "DRC") ||
        CONTAINS(STR(?class), "Rule") ||
        CONTAINS(STR(?class), "Violation") ||
        CONTAINS(STR(?class), "LVS") ||
        CONTAINS(STR(?class), "DesignRuleChecking")
    )
    OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?class
"""
    ),

    SPARQLQuery(
        name="verification_hierarchy",
        description="Get the Verification class hierarchy",
        domain="drc",
        expected_min_results=3,
        tags=["verification", "hierarchy"],
        query=PREFIXES + """
SELECT ?class ?label WHERE {
    ?class rdfs:subClassOf eda:Verification .
    OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?class
"""
    ),

    SPARQLQuery(
        name="verification_disjoint",
        description="Get classes disjoint with verification subclasses",
        domain="drc",
        expected_min_results=2,
        tags=["verification", "disjoint"],
        query=PREFIXES + """
SELECT DISTINCT ?class1 ?class2 WHERE {
    ?class1 rdfs:subClassOf eda:Verification .
    ?class1 owl:disjointWith ?class2 .
}
"""
    ),
]


# ============================================================================
# TEST/VERIFICATION DOMAIN QUERIES
# ============================================================================

TEST_QUERIES = [
    SPARQLQuery(
        name="test_classes",
        description="Get all test and verification related classes",
        domain="test",
        expected_min_results=3,
        tags=["test", "verification"],
        query=PREFIXES + """
SELECT DISTINCT ?class ?label WHERE {
    ?class a owl:Class .
    FILTER(
        CONTAINS(STR(?class), "Test") ||
        CONTAINS(STR(?class), "Simulation") ||
        CONTAINS(STR(?class), "Formal") ||
        CONTAINS(STR(?class), "DFT")
    )
    OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?class
"""
    ),

    SPARQLQuery(
        name="simulation_subclasses",
        description="Get subclasses of Simulation (if any)",
        domain="test",
        expected_min_results=0,
        tags=["test", "simulation"],
        query=PREFIXES + """
SELECT ?class ?label WHERE {
    ?class rdfs:subClassOf eda:Simulation .
    OPTIONAL { ?class rdfs:label ?label }
}
"""
    ),
]


# ============================================================================
# MANUFACTURING DOMAIN QUERIES
# ============================================================================

MANUFACTURING_QUERIES = [
    SPARQLQuery(
        name="manufacturing_classes",
        description="Get all manufacturing-related classes",
        domain="manufacturing",
        expected_min_results=3,
        tags=["manufacturing", "process"],
        query=PREFIXES + """
SELECT DISTINCT ?class ?label WHERE {
    ?class a owl:Class .
    FILTER(
        CONTAINS(STR(?class), "Litho") ||
        CONTAINS(STR(?class), "Etch") ||
        CONTAINS(STR(?class), "Material") ||
        CONTAINS(STR(?class), "Process") ||
        CONTAINS(STR(?class), "Fabrication") ||
        CONTAINS(STR(?class), "Manufacturing")
    )
    OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?class
"""
    ),
]


# ============================================================================
# SYSTEM DESIGN QUERIES
# ============================================================================

SYSTEM_QUERIES = [
    SPARQLQuery(
        name="system_classes",
        description="Get all system-level design classes",
        domain="system",
        expected_min_results=3,
        tags=["system", "chiplet"],
        query=PREFIXES + """
SELECT DISTINCT ?class ?label WHERE {
    ?class a owl:Class .
    FILTER(
        CONTAINS(STR(?class), "Chiplet") ||
        CONTAINS(STR(?class), "Interposer") ||
        CONTAINS(STR(?class), "Package") ||
        CONTAINS(STR(?class), "3D") ||
        CONTAINS(STR(?class), "Multi")
    )
    OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?class
"""
    ),

    SPARQLQuery(
        name="chiplet_properties",
        description="Get properties related to chiplets",
        domain="system",
        expected_min_results=1,
        tags=["system", "chiplet"],
        query=PREFIXES + """
SELECT ?prop ?range WHERE {
    ?prop rdfs:domain eda:Chiplet .
    OPTIONAL { ?prop rdfs:range ?range }
}
"""
    ),
]


# ============================================================================
# AUTOMATION/ML DOMAIN QUERIES
# ============================================================================

AUTOMATION_QUERIES = [
    SPARQLQuery(
        name="automation_classes",
        description="Get all automation and ML-related classes",
        domain="automation",
        expected_min_results=2,
        tags=["automation", "ml"],
        query=PREFIXES + """
SELECT DISTINCT ?class ?label WHERE {
    ?class a owl:Class .
    FILTER(
        CONTAINS(STR(?class), "Agent") ||
        CONTAINS(STR(?class), "Action") ||
        CONTAINS(STR(?class), "ML") ||
        CONTAINS(STR(?class), "MachineLearning") ||
        CONTAINS(STR(?class), "Heuristic") ||
        CONTAINS(STR(?class), "Automat")
    )
    OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?class
"""
    ),
]


# ============================================================================
# LIBRARY DOMAIN QUERIES
# ============================================================================

LIBRARY_QUERIES = [
    SPARQLQuery(
        name="library_classes",
        description="Get all library-related classes",
        domain="library",
        expected_min_results=3,
        tags=["library", "cell"],
        query=PREFIXES + """
SELECT DISTINCT ?class ?label WHERE {
    ?class a owl:Class .
    FILTER(
        CONTAINS(STR(?class), "Lib") ||
        CONTAINS(STR(?class), "Cell") ||
        CONTAINS(STR(?class), "Arc") ||
        CONTAINS(STR(?class), "LUT") ||
        CONTAINS(STR(?class), "Liberty")
    )
    OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?class
"""
    ),
]


# ============================================================================
# TOOLS AND FORMATS QUERIES
# ============================================================================

TOOLS_QUERIES = [
    SPARQLQuery(
        name="file_format_classes",
        description="Get all file format related classes",
        domain="tools-formats",
        expected_min_results=3,
        tags=["formats", "files"],
        query=PREFIXES + """
SELECT DISTINCT ?class ?label WHERE {
    ?class a owl:Class .
    FILTER(
        CONTAINS(STR(?class), "File") ||
        CONTAINS(STR(?class), "Format") ||
        CONTAINS(STR(?class), "LEF") ||
        CONTAINS(STR(?class), "DEF") ||
        CONTAINS(STR(?class), "GDSII") ||
        CONTAINS(STR(?class), "SPEF") ||
        CONTAINS(STR(?class), "Liberty")
    )
    OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?class
"""
    ),

    SPARQLQuery(
        name="tool_classes",
        description="Get all EDA tool related classes",
        domain="tools-formats",
        expected_min_results=1,
        tags=["tools"],
        query=PREFIXES + """
SELECT DISTINCT ?class ?label WHERE {
    ?class a owl:Class .
    FILTER(
        CONTAINS(STR(?class), "Synopsys") ||
        CONTAINS(STR(?class), "Cadence") ||
        CONTAINS(STR(?class), "Mentor") ||
        CONTAINS(STR(?class), "Tool")
    )
    OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?class
"""
    ),

    SPARQLQuery(
        name="tool_generates_artifact",
        description="Get tool-artifact generation relationships",
        domain="tools-formats",
        expected_min_results=1,
        tags=["tools", "artifacts"],
        query=PREFIXES + """
SELECT ?tool ?artifact WHERE {
    ?tool eda:generates ?artifact .
}
"""
    ),
]


# ============================================================================
# STATISTICS QUERIES
# ============================================================================

STATISTICS_QUERIES = [
    SPARQLQuery(
        name="class_count",
        description="Count total OWL classes",
        domain="statistics",
        expected_min_results=1,
        tags=["statistics"],
        query=PREFIXES + """
SELECT (COUNT(DISTINCT ?class) AS ?count) WHERE {
    ?class a owl:Class .
}
"""
    ),

    SPARQLQuery(
        name="property_counts",
        description="Count properties by type",
        domain="statistics",
        expected_min_results=1,
        tags=["statistics"],
        query=PREFIXES + """
SELECT
    (COUNT(DISTINCT ?objProp) AS ?objectProps)
    (COUNT(DISTINCT ?dataProp) AS ?dataProps)
WHERE {
    { ?objProp a owl:ObjectProperty }
    UNION
    { ?dataProp a owl:DatatypeProperty }
}
"""
    ),

    SPARQLQuery(
        name="disjoint_count",
        description="Count disjoint class axioms",
        domain="statistics",
        expected_min_results=1,
        tags=["statistics"],
        query=PREFIXES + """
SELECT (COUNT(*) AS ?count) WHERE {
    ?class1 owl:disjointWith ?class2 .
}
"""
    ),
]


# ============================================================================
# DISJOINTNESS QUERIES
# ============================================================================

DISJOINT_QUERIES = [
    SPARQLQuery(
        name="all_disjoint_classes",
        description="Get all disjoint class pairs",
        domain="disjoint",
        expected_min_results=5,
        tags=["disjoint", "consistency"],
        query=PREFIXES + """
SELECT ?class1 ?class2 WHERE {
    ?class1 owl:disjointWith ?class2 .
}
ORDER BY ?class1 ?class2
"""
    ),
]


# ============================================================================
# AGGREGATE ALL QUERIES
# ============================================================================

ALL_QUERIES = (
    CORE_QUERIES +
    TIMING_QUERIES +
    PHYSICAL_QUERIES +
    POWER_QUERIES +
    DRC_QUERIES +
    TEST_QUERIES +
    MANUFACTURING_QUERIES +
    SYSTEM_QUERIES +
    AUTOMATION_QUERIES +
    LIBRARY_QUERIES +
    TOOLS_QUERIES +
    STATISTICS_QUERIES +
    DISJOINT_QUERIES
)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_query_by_name(name: str) -> SPARQLQuery:
    """Get a query by its name."""
    for query in ALL_QUERIES:
        if query.name == name:
            return query
    raise ValueError(f"Query not found: {name}")


def get_queries_by_domain(domain: str) -> List[SPARQLQuery]:
    """Get all queries for a specific domain."""
    return [q for q in ALL_QUERIES if q.domain == domain]


def get_queries_by_tag(tag: str) -> List[SPARQLQuery]:
    """Get all queries with a specific tag."""
    return [q for q in ALL_QUERIES if tag in q.tags]


def get_all_domains() -> List[str]:
    """Get all unique domains."""
    return sorted(set(q.domain for q in ALL_QUERIES))


def get_all_tags() -> List[str]:
    """Get all unique tags."""
    tags = set()
    for q in ALL_QUERIES:
        tags.update(q.tags)
    return sorted(tags)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Display query catalog information."""
    print("=" * 70)
    print("MONOLITHIC EDA ONTOLOGY - SPARQL QUERY CATALOG")
    print("=" * 70)

    print(f"\nTotal Queries: {len(ALL_QUERIES)}")

    print("\nQueries by Domain:")
    for domain in get_all_domains():
        queries = get_queries_by_domain(domain)
        print(f"  {domain}: {len(queries)} queries")

    print("\nAll Tags:")
    print(f"  {', '.join(get_all_tags())}")

    print("\n--- Query List ---")
    for i, query in enumerate(ALL_QUERIES, 1):
        print(f"{i:3}. [{query.domain:15}] {query.name}")
        print(f"     {query.description}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
