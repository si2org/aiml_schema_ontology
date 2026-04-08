#!/usr/bin/env python3
"""
MCP Client for Monolithic EDA Ontology Server Testing

This module provides a client interface to interact with the EDA Ontology MCP Server
for testing, validation, and exploration of the monolithic EDA ontology.
"""

import asyncio
import json
import subprocess
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from contextlib import asynccontextmanager

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rdflib
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef


@dataclass
class QueryResult:
    """Container for SPARQL query results"""
    success: bool
    data: List[Dict[str, Any]]
    error: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class ValidationResult:
    """Container for validation results"""
    is_valid: bool
    syntax_valid: bool
    class_count: int
    property_count: int
    triple_count: int
    violations: List[str]
    warnings: List[str]


from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ONTOLOGY_PATH = REPO_ROOT / "ontology"


class MonolithicOntologyLoader:
    """
    Handles loading and parsing of the monolithic ontology file.
    Unlike the modular loader, this loads a single comprehensive file.
    """

    def __init__(self, base_path: str = str(DEFAULT_ONTOLOGY_PATH)):
        self.base_path = base_path
        self.graph = Graph()
        self.loaded_files: List[str] = []
        self.namespaces: Dict[str, str] = {}

        # Standard namespaces
        self.EDA = Namespace("http://example.org/eda#")
        self.graph.bind("eda", self.EDA)
        self.graph.bind("owl", OWL)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("rdf", RDF)

    def load_ontology(self, main_file: str = "eda-ontology.ttl", adapter_file: str = None) -> Tuple[bool, str]:
        """
        Load the monolithic ontology file and optional adapter.

        Args:
            main_file: Path to the main ontology file
            adapter_file: Optional path to adapter ontology

        Returns:
            Tuple of (success, message)
        """
        main_path = os.path.join(self.base_path, main_file)

        if not os.path.exists(main_path):
            return False, f"Main file not found: {main_path}"

        try:
            # Load main file
            self.graph.parse(main_path, format="turtle")
            self.loaded_files.append(main_file)

            # Load adapter if provided
            if adapter_file:
                adapter_path = os.path.join(self.base_path, adapter_file)
                if os.path.exists(adapter_path):
                    self.graph.parse(adapter_path, format="turtle")
                    self.loaded_files.append(adapter_file)

            # Extract namespaces
            for prefix, namespace in self.graph.namespaces():
                self.namespaces[str(prefix)] = str(namespace)

            return True, f"Loaded {len(self.graph)} triples from {len(self.loaded_files)} files"

        except Exception as e:
            return False, f"Error loading ontology: {str(e)}"

    def get_classes(self) -> List[str]:
        """Get all OWL classes defined in the ontology"""
        classes = set()
        for cls in self.graph.subjects(RDF.type, OWL.Class):
            if isinstance(cls, URIRef):
                classes.add(str(cls))
        for cls in self.graph.subjects(RDF.type, RDFS.Class):
            if isinstance(cls, URIRef):
                classes.add(str(cls))
        return sorted(classes)

    def get_properties(self) -> Dict[str, List[str]]:
        """Get all properties organized by type"""
        props = {
            "object": [],
            "datatype": [],
            "annotation": []
        }

        for prop in self.graph.subjects(RDF.type, OWL.ObjectProperty):
            if isinstance(prop, URIRef):
                props["object"].append(str(prop))

        for prop in self.graph.subjects(RDF.type, OWL.DatatypeProperty):
            if isinstance(prop, URIRef):
                props["datatype"].append(str(prop))

        for prop in self.graph.subjects(RDF.type, OWL.AnnotationProperty):
            if isinstance(prop, URIRef):
                props["annotation"].append(str(prop))

        return props

    def get_subclasses(self, parent_class: str) -> List[str]:
        """Get all subclasses of a given class"""
        parent_uri = URIRef(parent_class)
        subclasses = []

        for subclass in self.graph.subjects(RDFS.subClassOf, parent_uri):
            if isinstance(subclass, URIRef):
                subclasses.append(str(subclass))

        return subclasses

    def get_disjoint_classes(self, cls: str) -> List[str]:
        """Get classes that are disjoint with the given class"""
        cls_uri = URIRef(cls)
        disjoint = []

        for other in self.graph.objects(cls_uri, OWL.disjointWith):
            if isinstance(other, URIRef):
                disjoint.append(str(other))

        # Also check the reverse direction
        for other in self.graph.subjects(OWL.disjointWith, cls_uri):
            if isinstance(other, URIRef):
                disjoint.append(str(other))

        return list(set(disjoint))

    def query(self, sparql: str) -> QueryResult:
        """Execute a SPARQL query on the loaded ontology"""
        import time
        start = time.time()

        try:
            results = self.graph.query(sparql)
            data = []

            for row in results:
                row_dict = {}
                for var in results.vars:
                    value = getattr(row, str(var), None)
                    row_dict[str(var)] = str(value) if value else None
                data.append(row_dict)

            return QueryResult(
                success=True,
                data=data,
                execution_time=time.time() - start
            )
        except Exception as e:
            return QueryResult(
                success=False,
                data=[],
                error=str(e),
                execution_time=time.time() - start
            )

    def validate(self) -> ValidationResult:
        """Perform comprehensive validation of the loaded ontology"""
        violations = []
        warnings = []

        # Check for circular subclass relationships
        classes = self.get_classes()
        for cls in classes:
            visited = set()
            current = cls
            while True:
                if current in visited:
                    violations.append(f"Circular subclass: {cls}")
                    break
                visited.add(current)
                parents = list(self.graph.objects(URIRef(current), RDFS.subClassOf))
                if not parents:
                    break
                # Follow first parent (simplified check)
                parent = None
                for p in parents:
                    if isinstance(p, URIRef):
                        parent = str(p)
                        break
                if not parent:
                    break
                current = parent

        # Check for disjoint class violations
        disjoint_pairs = []
        for s, p, o in self.graph.triples((None, OWL.disjointWith, None)):
            if isinstance(s, URIRef) and isinstance(o, URIRef):
                disjoint_pairs.append((str(s), str(o)))

        for cls1, cls2 in disjoint_pairs:
            instances1 = set(str(s) for s in self.graph.subjects(RDF.type, URIRef(cls1)))
            instances2 = set(str(s) for s in self.graph.subjects(RDF.type, URIRef(cls2)))
            common = instances1 & instances2
            if common:
                violations.append(f"Instance in disjoint classes {cls1} and {cls2}: {common}")

        # Check for undefined domain/range references
        props = self.get_properties()
        all_props = props["object"] + props["datatype"]

        for prop in all_props:
            prop_uri = URIRef(prop)
            domains = list(self.graph.objects(prop_uri, RDFS.domain))
            ranges = list(self.graph.objects(prop_uri, RDFS.range))

            for domain in domains:
                if isinstance(domain, URIRef) and str(domain) not in classes:
                    if not str(domain).startswith("http://www.w3.org/"):
                        warnings.append(f"Property {prop} has undefined domain: {domain}")

            for rng in ranges:
                if isinstance(rng, URIRef) and str(rng) not in classes:
                    if not str(rng).startswith("http://www.w3.org/"):
                        warnings.append(f"Property {prop} has undefined range: {rng}")

        return ValidationResult(
            is_valid=len(violations) == 0,
            syntax_valid=True,
            class_count=len(classes),
            property_count=len(all_props),
            triple_count=len(self.graph),
            violations=violations,
            warnings=warnings
        )


class MCPOntologyClient:
    """
    Client for interacting with the Monolithic EDA Ontology MCP Server.
    Can run queries and validations either directly or through the server.
    """

    def __init__(self, ontology_path: str = str(DEFAULT_ONTOLOGY_PATH)):
        self.loader = MonolithicOntologyLoader(ontology_path)
        self.is_loaded = False

    def initialize(self, main_file: str = "eda-ontology.ttl", adapter_file: str = None) -> Tuple[bool, str]:
        """Initialize the client by loading the ontology"""
        success, message = self.loader.load_ontology(main_file, adapter_file)
        self.is_loaded = success
        return success, message

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the loaded ontology"""
        if not self.is_loaded:
            return {"error": "Ontology not loaded"}

        props = self.loader.get_properties()
        return {
            "triple_count": len(self.loader.graph),
            "file_count": len(self.loader.loaded_files),
            "files": self.loader.loaded_files,
            "class_count": len(self.loader.get_classes()),
            "object_property_count": len(props["object"]),
            "datatype_property_count": len(props["datatype"]),
            "annotation_property_count": len(props["annotation"]),
            "namespace_count": len(self.loader.namespaces)
        }

    def query(self, sparql: str) -> QueryResult:
        """Execute a SPARQL query"""
        if not self.is_loaded:
            return QueryResult(success=False, data=[], error="Ontology not loaded")
        return self.loader.query(sparql)

    def validate(self) -> ValidationResult:
        """Validate the ontology"""
        if not self.is_loaded:
            return ValidationResult(
                is_valid=False,
                syntax_valid=False,
                class_count=0,
                property_count=0,
                triple_count=0,
                violations=["Ontology not loaded"],
                warnings=[]
            )
        return self.loader.validate()

    def get_class_hierarchy(self, root_class: str = "http://example.org/eda#EDAProcess") -> Dict[str, Any]:
        """Get the class hierarchy starting from a root class"""
        if not self.is_loaded:
            return {"error": "Ontology not loaded"}

        def build_tree(cls: str, depth: int = 0) -> Dict[str, Any]:
            if depth > 10:  # Prevent infinite recursion
                return {"name": cls, "children": []}

            subclasses = self.loader.get_subclasses(cls)
            children = [build_tree(sub, depth + 1) for sub in subclasses]

            return {
                "name": cls.split("#")[-1] if "#" in cls else cls,
                "uri": cls,
                "children": children
            }

        return build_tree(root_class)

    def get_domain_modules(self) -> Dict[str, List[str]]:
        """Get entities organized by their domain (inferred from naming patterns)"""
        if not self.is_loaded:
            return {"error": "Ontology not loaded"}

        # Domain patterns from the ontology structure
        domains = {
            "core": [],
            "timing": [],
            "power": [],
            "physical": [],
            "drc": [],
            "test": [],
            "manufacturing": [],
            "system": [],
            "automation": [],
            "library": [],
            "tools-formats": []
        }

        # Map classes to domains based on naming patterns
        domain_keywords = {
            "timing": ["Timing", "Clock", "SDC", "Path", "Delay", "Corner", "Mode", "Slack"],
            "power": ["Power", "Voltage", "UPF", "Energy"],
            "physical": ["Physical", "Placement", "Routing", "CTS", "Floorplan", "Parasitic", "OPC", "Layout"],
            "drc": ["DRC", "Rule", "Violation", "LVS"],
            "test": ["Test", "Simulation", "Formal", "Verification", "DFT"],
            "manufacturing": ["Litho", "Etch", "Material", "Process", "Fabrication"],
            "system": ["Chiplet", "Interposer", "Package", "3D", "Multi"],
            "automation": ["Agent", "Action", "ML", "Heuristic", "Automat"],
            "library": ["Lib", "Cell", "Arc", "LUT", "Liberty"],
            "tools-formats": ["File", "Format", "Synopsys", "Cadence", "Mentor", "LEF", "DEF", "GDSII", "SPEF"]
        }

        for cls in self.loader.get_classes():
            cls_name = cls.split("#")[-1] if "#" in cls else cls
            assigned = False

            for domain, keywords in domain_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in cls_name.lower():
                        domains[domain].append(cls_name)
                        assigned = True
                        break
                if assigned:
                    break

            if not assigned:
                domains["core"].append(cls_name)

        return domains


# Reference SPARQL Queries for Testing
REFERENCE_QUERIES = {
    # Core ontology queries
    "all_classes": """
        PREFIX eda: <http://example.org/eda#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT DISTINCT ?class ?label WHERE {
            ?class a owl:Class .
            OPTIONAL { ?class rdfs:label ?label }
        }
        ORDER BY ?class
    """,

    "class_hierarchy": """
        PREFIX eda: <http://example.org/eda#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?class ?parent WHERE {
            ?class rdfs:subClassOf ?parent .
            FILTER(isURI(?parent))
        }
        ORDER BY ?parent ?class
    """,

    "eda_process_subclasses": """
        PREFIX eda: <http://example.org/eda#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?subclass WHERE {
            ?subclass rdfs:subClassOf eda:EDAProcess .
        }
    """,

    # Timing domain queries
    "timing_classes": """
        PREFIX eda: <http://example.org/eda#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?class WHERE {
            ?class a owl:Class .
            FILTER(CONTAINS(STR(?class), "Timing") ||
                   CONTAINS(STR(?class), "Clock") ||
                   CONTAINS(STR(?class), "Delay") ||
                   CONTAINS(STR(?class), "Path") ||
                   CONTAINS(STR(?class), "Slack"))
        }
    """,

    "timing_analysis_properties": """
        PREFIX eda: <http://example.org/eda#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?prop ?domain ?range WHERE {
            ?prop rdfs:domain eda:TimingAnalysis .
            OPTIONAL { ?prop rdfs:range ?range }
        }
    """,

    # Physical design queries
    "physical_design_subclasses": """
        PREFIX eda: <http://example.org/eda#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?subclass WHERE {
            ?subclass rdfs:subClassOf eda:PhysicalDesign .
        }
    """,

    "placement_disjoint_classes": """
        PREFIX eda: <http://example.org/eda#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT DISTINCT ?disjoint WHERE {
            eda:Placement owl:disjointWith ?disjoint .
        }
    """,

    # System design queries
    "chiplet_properties": """
        PREFIX eda: <http://example.org/eda#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?prop ?range WHERE {
            ?prop rdfs:domain eda:Chiplet .
            OPTIONAL { ?prop rdfs:range ?range }
        }
    """,

    "system_classes": """
        PREFIX eda: <http://example.org/eda#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT DISTINCT ?class WHERE {
            ?class a owl:Class .
            FILTER(CONTAINS(STR(?class), "Chiplet") ||
                   CONTAINS(STR(?class), "Interposer") ||
                   CONTAINS(STR(?class), "Package") ||
                   CONTAINS(STR(?class), "3D"))
        }
    """,

    # Library queries
    "library_structure": """
        PREFIX eda: <http://example.org/eda#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?class WHERE {
            ?class a owl:Class .
            FILTER(CONTAINS(STR(?class), "Lib") ||
                   CONTAINS(STR(?class), "Cell") ||
                   CONTAINS(STR(?class), "Liberty"))
        }
    """,

    # Tools and formats queries
    "tool_generates_artifact": """
        PREFIX eda: <http://example.org/eda#>
        SELECT ?tool ?artifact WHERE {
            ?tool eda:generates ?artifact .
        }
    """,

    "file_format_classes": """
        PREFIX eda: <http://example.org/eda#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT DISTINCT ?class WHERE {
            ?class a owl:Class .
            FILTER(CONTAINS(STR(?class), "File"))
        }
    """,

    # Verification queries
    "verification_subclasses": """
        PREFIX eda: <http://example.org/eda#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?subclass WHERE {
            ?subclass rdfs:subClassOf eda:Verification .
        }
    """,

    # Power domain queries
    "power_classes": """
        PREFIX eda: <http://example.org/eda#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT DISTINCT ?class WHERE {
            ?class a owl:Class .
            FILTER(CONTAINS(STR(?class), "Power") ||
                   CONTAINS(STR(?class), "UPF") ||
                   CONTAINS(STR(?class), "Voltage"))
        }
    """,

    # Object properties
    "all_object_properties": """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?prop ?domain ?range WHERE {
            ?prop a owl:ObjectProperty .
            OPTIONAL { ?prop rdfs:domain ?domain }
            OPTIONAL { ?prop rdfs:range ?range }
        }
        ORDER BY ?prop
    """,

    # Datatype properties
    "all_datatype_properties": """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?prop ?domain ?range WHERE {
            ?prop a owl:DatatypeProperty .
            OPTIONAL { ?prop rdfs:domain ?domain }
            OPTIONAL { ?prop rdfs:range ?range }
        }
        ORDER BY ?prop
    """,

    # Disjointness queries
    "all_disjoint_classes": """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT ?class1 ?class2 WHERE {
            ?class1 owl:disjointWith ?class2 .
        }
        ORDER BY ?class1 ?class2
    """,

    # Statistics queries
    "class_count": """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT (COUNT(DISTINCT ?class) AS ?count) WHERE {
            ?class a owl:Class .
        }
    """,

    "property_count": """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT
            (COUNT(DISTINCT ?objProp) AS ?objectProps)
            (COUNT(DISTINCT ?dataProp) AS ?dataProps)
        WHERE {
            { ?objProp a owl:ObjectProperty }
            UNION
            { ?dataProp a owl:DatatypeProperty }
        }
    """
}


def main():
    """Main entry point for testing the client"""
    print("=" * 60)
    print("Monolithic EDA Ontology MCP Client")
    print("=" * 60)

    # Initialize client
    client = MCPOntologyClient()
    success, message = client.initialize("eda-ontology.ttl", "eda-ontology-adapter.ttl")

    if not success:
        print(f"Failed to initialize: {message}")
        return 1

    print(f"\n{message}")

    # Get stats
    print("\n--- Ontology Statistics ---")
    stats = client.get_stats()
    for key, value in stats.items():
        if key != "files":
            print(f"  {key}: {value}")
    print(f"  files: {', '.join(stats['files'])}")

    # Run validation
    print("\n--- Validation Results ---")
    validation = client.validate()
    print(f"  Valid: {validation.is_valid}")
    print(f"  Classes: {validation.class_count}")
    print(f"  Properties: {validation.property_count}")
    print(f"  Triples: {validation.triple_count}")

    if validation.violations:
        print(f"  Violations ({len(validation.violations)}):")
        for v in validation.violations[:5]:
            print(f"    - {v}")

    if validation.warnings:
        print(f"  Warnings ({len(validation.warnings)}):")
        for w in validation.warnings[:5]:
            print(f"    - {w}")

    # Run sample queries
    print("\n--- Sample Query Results ---")

    # Test a few queries
    test_queries = ["eda_process_subclasses", "placement_disjoint_classes", "tool_generates_artifact"]

    for query_name in test_queries:
        print(f"\n  Query: {query_name}")
        result = client.query(REFERENCE_QUERIES[query_name])
        if result.success:
            print(f"    Results: {len(result.data)} rows ({result.execution_time:.3f}s)")
            for row in result.data[:3]:
                print(f"      {row}")
            if len(result.data) > 3:
                print(f"      ... and {len(result.data) - 3} more")
        else:
            print(f"    Error: {result.error}")

    # Show domain modules
    print("\n--- Domain Distribution ---")
    domains = client.get_domain_modules()
    for domain, entities in domains.items():
        if entities and not isinstance(entities, str):  # Skip error message
            print(f"  {domain}: {len(entities)} entities")

    return 0


if __name__ == "__main__":
    sys.exit(main())
