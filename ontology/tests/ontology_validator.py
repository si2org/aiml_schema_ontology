#!/usr/bin/env python3
"""
Comprehensive Ontology Validator for Monolithic EDA Ontology

This module provides deep validation capabilities for OWL ontologies,
including syntax checking, semantic validation, and consistency analysis.
Designed for the monolithic EDA ontology architecture.
"""

import os
import sys
from typing import Dict, List, Tuple, Set, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict

import rdflib
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, Literal, BNode
from rdflib.namespace import XSD


@dataclass
class OntologyMetrics:
    """Metrics about the ontology structure"""
    total_triples: int = 0
    class_count: int = 0
    object_property_count: int = 0
    datatype_property_count: int = 0
    annotation_property_count: int = 0
    individual_count: int = 0
    restriction_count: int = 0
    disjoint_axiom_count: int = 0
    max_hierarchy_depth: int = 0
    avg_hierarchy_depth: float = 0.0
    unique_subjects: int = 0
    unique_predicates: int = 0
    unique_objects: int = 0


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'syntax', 'semantic', 'consistency', 'best_practice'
    message: str
    location: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationReport:
    """Complete validation report"""
    is_valid: bool
    syntax_valid: bool
    semantic_valid: bool
    metrics: OntologyMetrics
    issues: List[ValidationIssue] = field(default_factory=list)
    namespaces: Dict[str, str] = field(default_factory=dict)
    classes: List[str] = field(default_factory=list)
    properties: Dict[str, List[str]] = field(default_factory=dict)


class EDAOntologyValidator:
    """
    Comprehensive validator for the monolithic EDA ontology.
    Performs syntax, semantic, and domain-specific validation.
    """

    # Expected EDA ontology domains (inferred from class patterns)
    EXPECTED_DOMAINS = [
        "core", "timing", "power", "physical", "drc", "test",
        "manufacturing", "system", "automation", "library", "tools-formats"
    ]

    # Core classes that must exist
    REQUIRED_CLASSES = [
        "http://example.org/eda#EDAProcess",
        "http://example.org/eda#DesignArtifact",
        "http://example.org/eda#Tool",
        "http://example.org/eda#Metric",
        "http://example.org/eda#Flow",
        "http://example.org/eda#Design",
        "http://example.org/eda#Netlist"
    ]

    # Required properties
    REQUIRED_PROPERTIES = [
        "http://example.org/eda#consumes",
        "http://example.org/eda#produces",
        "http://example.org/eda#hasInstance",
        "http://example.org/eda#hasNet",
        "http://example.org/eda#hasPort"
    ]

    def __init__(self, base_path: str = "onto"):
        self.base_path = base_path
        self.graph = Graph()
        self.EDA = Namespace("http://example.org/eda#")
        self.issues: List[ValidationIssue] = []
        self.metrics = OntologyMetrics()
        self.loaded_files: List[str] = []

    def load_ontology(self, main_file: str = "eda_ontology.ttl", adapter_file: str = None) -> bool:
        """Load the monolithic ontology and optional adapter"""
        main_path = os.path.join(self.base_path, main_file)

        if not os.path.exists(main_path):
            self.issues.append(ValidationIssue(
                severity="error",
                category="syntax",
                message=f"Main ontology file not found: {main_path}"
            ))
            return False

        try:
            # Load main file
            self.graph.parse(main_path, format="turtle")
            self.loaded_files.append(main_file)

            # Load adapter if provided and exists
            if adapter_file:
                adapter_path = os.path.join(self.base_path, adapter_file)
                if os.path.exists(adapter_path):
                    try:
                        self.graph.parse(adapter_path, format="turtle")
                        self.loaded_files.append(adapter_file)
                    except Exception as e:
                        self.issues.append(ValidationIssue(
                            severity="warning",
                            category="syntax",
                            message=f"Failed to parse adapter {adapter_file}: {str(e)}",
                            location=adapter_file
                        ))

            return True

        except Exception as e:
            self.issues.append(ValidationIssue(
                severity="error",
                category="syntax",
                message=f"Failed to parse main file: {str(e)}",
                location=main_file
            ))
            return False

    def validate(self) -> ValidationReport:
        """Run all validation checks and return report"""
        self.issues = []

        # 1. Calculate metrics
        self._calculate_metrics()

        # 2. Validate required elements
        self._validate_required_classes()
        self._validate_required_properties()

        # 3. Semantic validation
        self._validate_class_hierarchy()
        self._validate_property_definitions()
        self._validate_disjointness()
        self._validate_domain_range()

        # 4. Domain-specific validation
        self._validate_eda_domains()

        # 5. Best practices
        self._check_best_practices()

        # Determine overall validity
        has_errors = any(i.severity == "error" for i in self.issues)
        has_semantic_errors = any(
            i.severity == "error" and i.category == "semantic"
            for i in self.issues
        )

        # Collect classes and properties
        classes = self._get_all_classes()
        properties = self._get_all_properties()
        namespaces = {str(p): str(n) for p, n in self.graph.namespaces()}

        return ValidationReport(
            is_valid=not has_errors,
            syntax_valid=not any(i.category == "syntax" and i.severity == "error" for i in self.issues),
            semantic_valid=not has_semantic_errors,
            metrics=self.metrics,
            issues=self.issues,
            namespaces=namespaces,
            classes=classes,
            properties=properties
        )

    def _calculate_metrics(self):
        """Calculate ontology metrics"""
        # Basic counts
        self.metrics.total_triples = len(self.graph)
        self.metrics.unique_subjects = len(set(self.graph.subjects()))
        self.metrics.unique_predicates = len(set(self.graph.predicates()))
        self.metrics.unique_objects = len(set(self.graph.objects()))

        # Class count
        classes = set()
        for cls in self.graph.subjects(RDF.type, OWL.Class):
            if isinstance(cls, URIRef):
                classes.add(cls)
        for cls in self.graph.subjects(RDF.type, RDFS.Class):
            if isinstance(cls, URIRef):
                classes.add(cls)
        self.metrics.class_count = len(classes)

        # Property counts
        self.metrics.object_property_count = len(list(
            self.graph.subjects(RDF.type, OWL.ObjectProperty)
        ))
        self.metrics.datatype_property_count = len(list(
            self.graph.subjects(RDF.type, OWL.DatatypeProperty)
        ))
        self.metrics.annotation_property_count = len(list(
            self.graph.subjects(RDF.type, OWL.AnnotationProperty)
        ))

        # Restriction count
        self.metrics.restriction_count = len(list(
            self.graph.subjects(RDF.type, OWL.Restriction)
        ))

        # Disjoint axiom count
        self.metrics.disjoint_axiom_count = len(list(
            self.graph.triples((None, OWL.disjointWith, None))
        ))

        # Calculate hierarchy depths
        depths = self._calculate_hierarchy_depths(classes)
        if depths:
            self.metrics.max_hierarchy_depth = max(depths.values())
            self.metrics.avg_hierarchy_depth = sum(depths.values()) / len(depths)

    def _calculate_hierarchy_depths(self, classes: Set[URIRef]) -> Dict[str, int]:
        """Calculate depth of each class in the hierarchy"""
        depths = {}

        def get_depth(cls: URIRef, visited: Set[URIRef] = None) -> int:
            if visited is None:
                visited = set()

            if cls in visited:
                return 0  # Cycle detected

            visited.add(cls)
            parents = [
                p for p in self.graph.objects(cls, RDFS.subClassOf)
                if isinstance(p, URIRef)
            ]

            if not parents:
                return 1

            max_parent_depth = 0
            for parent in parents:
                parent_depth = get_depth(parent, visited.copy())
                max_parent_depth = max(max_parent_depth, parent_depth)

            return max_parent_depth + 1

        for cls in classes:
            depths[str(cls)] = get_depth(cls)

        return depths

    def _validate_required_classes(self):
        """Check that all required classes exist"""
        for cls_uri in self.REQUIRED_CLASSES:
            cls = URIRef(cls_uri)
            if (cls, RDF.type, OWL.Class) not in self.graph:
                self.issues.append(ValidationIssue(
                    severity="error",
                    category="semantic",
                    message=f"Required class not found: {cls_uri}",
                    suggestion="Ensure the ontology includes core EDA concepts"
                ))

    def _validate_required_properties(self):
        """Check that all required properties exist"""
        for prop_uri in self.REQUIRED_PROPERTIES:
            prop = URIRef(prop_uri)
            is_obj_prop = (prop, RDF.type, OWL.ObjectProperty) in self.graph
            is_data_prop = (prop, RDF.type, OWL.DatatypeProperty) in self.graph

            if not (is_obj_prop or is_data_prop):
                self.issues.append(ValidationIssue(
                    severity="warning",
                    category="semantic",
                    message=f"Required property not found: {prop_uri}",
                    suggestion="Check the ontology for property definitions"
                ))

    def _validate_class_hierarchy(self):
        """Validate class hierarchy for issues"""
        # Check for circular subclass relationships
        classes = [
            cls for cls in self.graph.subjects(RDF.type, OWL.Class)
            if isinstance(cls, URIRef)
        ]

        for cls in classes:
            visited = []
            current = cls

            while current:
                if current in visited:
                    cycle = " -> ".join(str(c).split("#")[-1] for c in visited)
                    self.issues.append(ValidationIssue(
                        severity="error",
                        category="semantic",
                        message=f"Circular subclass relationship detected: {cycle}",
                        location=str(cls)
                    ))
                    break

                visited.append(current)
                parents = [
                    p for p in self.graph.objects(current, RDFS.subClassOf)
                    if isinstance(p, URIRef)
                ]
                current = parents[0] if parents else None

        # Check for orphan classes (no parent, not a top-level class)
        top_level = {
            URIRef("http://example.org/eda#EDAProcess"),
            URIRef("http://example.org/eda#DesignArtifact"),
            URIRef("http://example.org/eda#Tool"),
            URIRef("http://example.org/eda#Metric")
        }

        for cls in classes:
            if cls not in top_level:
                parents = list(self.graph.objects(cls, RDFS.subClassOf))
                if not any(isinstance(p, URIRef) for p in parents):
                    # Check if it's used as a domain/range (might be external)
                    if str(cls).startswith("http://example.org/eda"):
                        self.issues.append(ValidationIssue(
                            severity="info",
                            category="best_practice",
                            message=f"Class has no parent: {cls}",
                            suggestion="Consider adding rdfs:subClassOf relationship"
                        ))

    def _validate_property_definitions(self):
        """Validate property definitions"""
        # Check object properties
        for prop in self.graph.subjects(RDF.type, OWL.ObjectProperty):
            if isinstance(prop, URIRef):
                # Check for domain
                domains = list(self.graph.objects(prop, RDFS.domain))
                if not domains:
                    self.issues.append(ValidationIssue(
                        severity="info",
                        category="best_practice",
                        message=f"Object property has no domain: {prop}",
                        suggestion="Consider adding rdfs:domain"
                    ))

                # Check for range
                ranges = list(self.graph.objects(prop, RDFS.range))
                if not ranges:
                    self.issues.append(ValidationIssue(
                        severity="info",
                        category="best_practice",
                        message=f"Object property has no range: {prop}",
                        suggestion="Consider adding rdfs:range"
                    ))

        # Check datatype properties
        for prop in self.graph.subjects(RDF.type, OWL.DatatypeProperty):
            if isinstance(prop, URIRef):
                ranges = list(self.graph.objects(prop, RDFS.range))
                for rng in ranges:
                    # Check that range is a datatype
                    if isinstance(rng, URIRef):
                        if not str(rng).startswith("http://www.w3.org/2001/XMLSchema"):
                            self.issues.append(ValidationIssue(
                                severity="warning",
                                category="semantic",
                                message=f"Datatype property {prop} has non-XSD range: {rng}",
                                suggestion="Use XSD datatypes for datatype properties"
                            ))

    def _validate_disjointness(self):
        """Validate disjoint class axioms"""
        disjoint_pairs = []

        for s, p, o in self.graph.triples((None, OWL.disjointWith, None)):
            if isinstance(s, URIRef) and isinstance(o, URIRef):
                disjoint_pairs.append((s, o))

        # Check for violations (individuals belonging to disjoint classes)
        for cls1, cls2 in disjoint_pairs:
            instances1 = set(self.graph.subjects(RDF.type, cls1))
            instances2 = set(self.graph.subjects(RDF.type, cls2))

            common = instances1 & instances2
            for instance in common:
                self.issues.append(ValidationIssue(
                    severity="error",
                    category="consistency",
                    message=f"Individual {instance} belongs to disjoint classes {cls1} and {cls2}",
                    location=str(instance)
                ))

        # Verify expected disjoint relationships in EDA ontology
        expected_disjoint = [
            ("LogicalDesign", "PhysicalDesign"),
            ("Verification", "LogicalSynthesis"),
            ("Simulation", "FormalVerification"),
            ("Placement", "Routing")
        ]

        for cls1_name, cls2_name in expected_disjoint:
            cls1 = URIRef(f"http://example.org/eda#{cls1_name}")
            cls2 = URIRef(f"http://example.org/eda#{cls2_name}")

            if (cls1, OWL.disjointWith, cls2) not in self.graph and \
               (cls2, OWL.disjointWith, cls1) not in self.graph:
                self.issues.append(ValidationIssue(
                    severity="info",
                    category="semantic",
                    message=f"Expected disjointness not found: {cls1_name} and {cls2_name}",
                    suggestion="Verify if these classes should be disjoint"
                ))

    def _validate_domain_range(self):
        """Validate domain/range consistency"""
        for prop in self.graph.subjects(RDF.type, OWL.ObjectProperty):
            if not isinstance(prop, URIRef):
                continue

            domains = list(self.graph.objects(prop, RDFS.domain))
            ranges = list(self.graph.objects(prop, RDFS.range))

            # Check property usage
            for s, p, o in self.graph.triples((None, prop, None)):
                # Check domain constraint
                for domain in domains:
                    if isinstance(domain, URIRef):
                        subject_types = list(self.graph.objects(s, RDF.type))
                        if domain not in subject_types:
                            # Check for subclass
                            is_subclass = self._is_subclass_of(s, domain)
                            if not is_subclass:
                                self.issues.append(ValidationIssue(
                                    severity="warning",
                                    category="consistency",
                                    message=f"Subject {s} of property {prop} may not match domain {domain}",
                                    location=str(s)
                                ))

                # Check range constraint
                if isinstance(o, URIRef):
                    for rng in ranges:
                        if isinstance(rng, URIRef):
                            object_types = list(self.graph.objects(o, RDF.type))
                            if rng not in object_types:
                                is_subclass = self._is_subclass_of(o, rng)
                                if not is_subclass:
                                    self.issues.append(ValidationIssue(
                                        severity="warning",
                                        category="consistency",
                                        message=f"Object {o} of property {prop} may not match range {rng}",
                                        location=str(o)
                                    ))

    def _is_subclass_of(self, entity: URIRef, target_class: URIRef) -> bool:
        """Check if entity's type is a subclass of target_class"""
        entity_types = list(self.graph.objects(entity, RDF.type))

        for entity_type in entity_types:
            if entity_type == target_class:
                return True
            if isinstance(entity_type, URIRef):
                # Check subclass chain
                visited = set()
                to_check = [entity_type]
                while to_check:
                    current = to_check.pop()
                    if current in visited:
                        continue
                    visited.add(current)
                    if current == target_class:
                        return True
                    parents = [
                        p for p in self.graph.objects(current, RDFS.subClassOf)
                        if isinstance(p, URIRef)
                    ]
                    to_check.extend(parents)
        return False

    def _validate_eda_domains(self):
        """Validate EDA-specific domain coverage"""
        domain_patterns = {
            "timing": ["Timing", "Clock", "SDC", "Path", "Delay"],
            "power": ["Power", "Voltage", "UPF", "Energy"],
            "physical": ["Physical", "Placement", "Routing", "CTS", "Floorplan"],
            "verification": ["Verification", "Simulation", "Formal", "DRC", "LVS"],
            "library": ["Library", "Cell", "Liberty"],
            "manufacturing": ["Manufacturing", "Litho", "Etch", "Process"]
        }

        classes = self._get_all_classes()
        class_names = [c.split("#")[-1] for c in classes]

        for domain, patterns in domain_patterns.items():
            found = any(
                any(pattern.lower() in cn.lower() for pattern in patterns)
                for cn in class_names
            )
            if not found:
                self.issues.append(ValidationIssue(
                    severity="warning",
                    category="semantic",
                    message=f"EDA domain '{domain}' may not be fully covered",
                    suggestion=f"Consider adding classes for: {', '.join(patterns)}"
                ))

    def _check_best_practices(self):
        """Check for ontology best practices"""
        # Check for labels
        classes = self._get_all_classes()
        for cls in classes:
            cls_uri = URIRef(cls)
            labels = list(self.graph.objects(cls_uri, RDFS.label))
            if not labels:
                self.issues.append(ValidationIssue(
                    severity="info",
                    category="best_practice",
                    message=f"Class has no rdfs:label: {cls}",
                    suggestion="Add rdfs:label for documentation"
                ))

        # Check for comments on top-level classes
        top_level = [
            "http://example.org/eda#EDAProcess",
            "http://example.org/eda#DesignArtifact",
            "http://example.org/eda#Tool",
            "http://example.org/eda#Metric"
        ]
        for cls in top_level:
            cls_uri = URIRef(cls)
            comments = list(self.graph.objects(cls_uri, RDFS.comment))
            if not comments:
                self.issues.append(ValidationIssue(
                    severity="info",
                    category="best_practice",
                    message=f"Top-level class has no rdfs:comment: {cls}",
                    suggestion="Add rdfs:comment for documentation"
                ))

    def _get_all_classes(self) -> List[str]:
        """Get all classes in the ontology"""
        classes = set()
        for cls in self.graph.subjects(RDF.type, OWL.Class):
            if isinstance(cls, URIRef):
                classes.add(str(cls))
        for cls in self.graph.subjects(RDF.type, RDFS.Class):
            if isinstance(cls, URIRef):
                classes.add(str(cls))
        return sorted(classes)

    def _get_all_properties(self) -> Dict[str, List[str]]:
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


def validate_ontology(path: str = "onto", main_file: str = "eda_ontology.ttl",
                     adapter_file: str = None) -> Tuple[bool, str, ValidationReport]:
    """
    Convenience function to validate the monolithic ontology.

    Args:
        path: Path to ontology directory
        main_file: Main ontology filename
        adapter_file: Optional adapter filename

    Returns:
        Tuple of (is_valid, report_text, ValidationReport)
    """
    validator = EDAOntologyValidator(path)

    if not validator.load_ontology(main_file, adapter_file):
        report = ValidationReport(
            is_valid=False,
            syntax_valid=False,
            semantic_valid=False,
            metrics=validator.metrics,
            issues=validator.issues
        )
        return False, "Failed to load ontology", report

    report = validator.validate()

    # Generate text report
    lines = []
    lines.append("=" * 70)
    lines.append("MONOLITHIC EDA ONTOLOGY VALIDATION REPORT")
    lines.append("=" * 70)

    lines.append(f"\n{'Files:':<20} {', '.join(validator.loaded_files)}")
    lines.append(f"{'Syntax Valid:':<20} {'Yes' if report.syntax_valid else 'No'}")
    lines.append(f"{'Semantic Valid:':<20} {'Yes' if report.semantic_valid else 'No'}")
    lines.append(f"{'Overall Valid:':<20} {'Yes' if report.is_valid else 'No'}")

    lines.append(f"\n{'--- METRICS ---':^70}")
    m = report.metrics
    lines.append(f"  Total Triples:        {m.total_triples}")
    lines.append(f"  Classes:              {m.class_count}")
    lines.append(f"  Object Properties:    {m.object_property_count}")
    lines.append(f"  Datatype Properties:  {m.datatype_property_count}")
    lines.append(f"  Annotation Properties:{m.annotation_property_count}")
    lines.append(f"  Restrictions:         {m.restriction_count}")
    lines.append(f"  Disjoint Axioms:      {m.disjoint_axiom_count}")
    lines.append(f"  Max Hierarchy Depth:  {m.max_hierarchy_depth}")
    lines.append(f"  Avg Hierarchy Depth:  {m.avg_hierarchy_depth:.2f}")

    # Count issues by severity
    errors = [i for i in report.issues if i.severity == "error"]
    warnings = [i for i in report.issues if i.severity == "warning"]
    infos = [i for i in report.issues if i.severity == "info"]

    lines.append(f"\n{'--- ISSUES ---':^70}")
    lines.append(f"  Errors:   {len(errors)}")
    lines.append(f"  Warnings: {len(warnings)}")
    lines.append(f"  Info:     {len(infos)}")

    if errors:
        lines.append(f"\n{'ERRORS:':}")
        for e in errors[:10]:
            lines.append(f"  - [{e.category}] {e.message}")
            if e.suggestion:
                lines.append(f"    Suggestion: {e.suggestion}")

    if warnings:
        lines.append(f"\n{'WARNINGS:':}")
        for w in warnings[:10]:
            lines.append(f"  - [{w.category}] {w.message}")

    lines.append("\n" + "=" * 70)

    report_text = "\n".join(lines)
    return report.is_valid, report_text, report


def main():
    """Main entry point for command-line validation."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Validate Monolithic EDA Ontology")
    parser.add_argument("--path", default="onto", help="Path to ontology directory")
    parser.add_argument("--file", default="eda_ontology.ttl", help="Main ontology file")
    parser.add_argument("--adapter", default=None, help="Adapter ontology file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    is_valid, report_text, report = validate_ontology(args.path, args.file, args.adapter)

    if args.json:
        output = {
            "is_valid": report.is_valid,
            "syntax_valid": report.syntax_valid,
            "semantic_valid": report.semantic_valid,
            "metrics": {
                "total_triples": report.metrics.total_triples,
                "class_count": report.metrics.class_count,
                "object_property_count": report.metrics.object_property_count,
                "datatype_property_count": report.metrics.datatype_property_count,
                "restriction_count": report.metrics.restriction_count,
                "disjoint_axiom_count": report.metrics.disjoint_axiom_count,
            },
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "message": i.message,
                    "suggestion": i.suggestion
                }
                for i in report.issues
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        print(report_text)

    return 0 if is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
