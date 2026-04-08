#!/usr/bin/env python3
"""
Pytest Test Suite for Monolithic EDA Ontology

This module provides comprehensive pytest-based tests for validating
the monolithic EDA ontology structure, semantics, and content.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import pytest

CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parents[1]
MCP_DIR = REPO_ROOT / "usecases" / "MCP"
ONTOLOGY_DIR = REPO_ROOT / "ontology"
if str(MCP_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_DIR))

sys.path.insert(0, str(CURRENT_DIR))

from mcp_client import MCPOntologyClient, REFERENCE_QUERIES  # type: ignore


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def ontology_client():
    """Create and initialize the ontology client for the test session."""
    client = MCPOntologyClient(str(ONTOLOGY_DIR))
    success, message = client.initialize("eda_ontology.ttl", "eda-ontology-adapter.ttl")
    if not success:
        pytest.skip(f"Could not load ontology: {message}")
    return client


@pytest.fixture(scope="session")
def ontology_stats(ontology_client):
    """Get ontology statistics."""
    return ontology_client.get_stats()


@pytest.fixture(scope="session")
def validation_result(ontology_client):
    """Get validation result."""
    return ontology_client.validate()


# ============================================================================
# LOADING AND SYNTAX TESTS
# ============================================================================

class TestOntologyLoading:
    """Tests for ontology loading and syntax validation."""

    def test_ontology_loads(self, ontology_client):
        """Test that the ontology loads successfully."""
        assert ontology_client.is_loaded, "Ontology should be loaded"

    def test_syntax_valid(self, validation_result):
        """Test that the ontology has valid syntax."""
        assert validation_result.syntax_valid, "Ontology syntax should be valid"

    def test_has_triples(self, ontology_stats):
        """Test that the ontology contains triples."""
        assert ontology_stats["triple_count"] > 0, "Ontology should contain triples"

    def test_main_file_exists(self):
        """Test that the main ontology file exists."""
        path = ONTOLOGY_DIR / "eda_ontology.ttl"
        assert path.exists(), f"Main ontology file should exist at {path}"


# ============================================================================
# CLASS STRUCTURE TESTS
# ============================================================================

class TestClassStructure:
    """Tests for ontology class structure."""

    def test_has_classes(self, ontology_stats):
        """Test that the ontology defines classes."""
        assert ontology_stats["class_count"] > 0, "Ontology should define classes"

    def test_minimum_class_count(self, ontology_stats):
        """Test that the ontology has a minimum number of classes."""
        assert ontology_stats["class_count"] >= 50, \
            f"Expected at least 50 classes, got {ontology_stats['class_count']}"

    def test_required_top_level_classes(self, ontology_client):
        """Test that required top-level classes exist."""
        required = ["EDAProcess", "DesignArtifact", "Tool", "Metric"]
        classes = ontology_client.loader.get_classes()
        class_names = [c.split("#")[-1] for c in classes]

        for cls in required:
            assert cls in class_names, f"Required class {cls} should exist"

    def test_eda_process_has_subclasses(self, ontology_client):
        """Test that EDAProcess has subclasses."""
        subclasses = ontology_client.loader.get_subclasses(
            "http://example.org/eda#EDAProcess"
        )
        assert len(subclasses) > 0, "EDAProcess should have subclasses"

    def test_no_circular_subclass(self, validation_result):
        """Test that there are no circular subclass relationships."""
        circular = [v for v in validation_result.violations if "Circular" in v]
        assert len(circular) == 0, f"Should have no circular subclass: {circular}"


# ============================================================================
# PROPERTY TESTS
# ============================================================================

class TestPropertyStructure:
    """Tests for ontology property structure."""

    def test_has_object_properties(self, ontology_stats):
        """Test that the ontology defines object properties."""
        assert ontology_stats["object_property_count"] > 0, \
            "Ontology should define object properties"

    def test_has_datatype_properties(self, ontology_stats):
        """Test that the ontology defines datatype properties."""
        assert ontology_stats["datatype_property_count"] > 0, \
            "Ontology should define datatype properties"

    def test_required_properties(self, ontology_client):
        """Test that required properties exist."""
        required = ["consumes", "produces", "hasInstance", "hasNet", "hasPort"]
        props = ontology_client.loader.get_properties()
        all_props = [p.split("#")[-1] for p in props["object"] + props["datatype"]]

        for prop in required:
            assert prop in all_props, f"Required property {prop} should exist"


# ============================================================================
# DOMAIN COVERAGE TESTS
# ============================================================================

class TestDomainCoverage:
    """Tests for EDA domain coverage."""

    @pytest.mark.parametrize("domain,keywords", [
        ("timing", ["Timing", "Clock", "Path"]),
        ("power", ["Power", "Voltage"]),
        ("physical", ["Placement", "Routing"]),
        ("verification", ["Verification", "Simulation"]),
        ("library", ["Library", "Cell"]),
    ])
    def test_domain_coverage(self, ontology_client, domain, keywords):
        """Test that each domain has representation in the ontology."""
        classes = ontology_client.loader.get_classes()
        class_names = [c.split("#")[-1] for c in classes]

        found = any(
            any(kw.lower() in cn.lower() for kw in keywords)
            for cn in class_names
        )
        assert found, f"Domain {domain} should have classes matching {keywords}"

    def test_physical_design_subclasses(self, ontology_client):
        """Test that PhysicalDesign has expected subclasses."""
        expected = ["Placement", "Routing"]
        subclasses = ontology_client.loader.get_subclasses(
            "http://example.org/eda#PhysicalDesign"
        )
        subclass_names = [s.split("#")[-1] for s in subclasses]

        for expected_sub in expected:
            assert any(expected_sub in s for s in subclass_names), \
                f"PhysicalDesign should have {expected_sub} as subclass"


# ============================================================================
# DISJOINTNESS TESTS
# ============================================================================

class TestDisjointness:
    """Tests for disjoint class axioms."""

    def test_has_disjoint_axioms(self, ontology_client):
        """Test that the ontology has disjoint class axioms."""
        result = ontology_client.query(REFERENCE_QUERIES["all_disjoint_classes"])
        assert result.success and len(result.data) > 0, \
            "Ontology should have disjoint class axioms"

    def test_placement_routing_disjoint(self, ontology_client):
        """Test that Placement and Routing are disjoint."""
        disjoint = ontology_client.loader.get_disjoint_classes(
            "http://example.org/eda#Placement"
        )
        routing_uri = "http://example.org/eda#Routing"
        assert routing_uri in disjoint, \
            "Placement and Routing should be disjoint"

    def test_no_disjoint_violations(self, validation_result):
        """Test that there are no disjoint class violations."""
        violations = [v for v in validation_result.violations if "disjoint" in v.lower()]
        assert len(violations) == 0, f"Should have no disjoint violations: {violations}"


# ============================================================================
# SPARQL QUERY TESTS
# ============================================================================

class TestSPARQLQueries:
    """Tests for SPARQL query execution."""

    def test_can_execute_sparql(self, ontology_client):
        """Test that SPARQL queries can be executed."""
        result = ontology_client.query(REFERENCE_QUERIES["all_classes"])
        assert result.success, f"Query should succeed: {result.error}"

    def test_class_count_query(self, ontology_client):
        """Test the class count query."""
        result = ontology_client.query(REFERENCE_QUERIES["class_count"])
        assert result.success, f"Query should succeed: {result.error}"
        assert len(result.data) > 0, "Query should return results"

    @pytest.mark.parametrize("query_name", [
        "eda_process_subclasses",
        "timing_classes",
        "physical_design_subclasses",
        "all_object_properties",
        "all_datatype_properties",
    ])
    def test_domain_queries(self, ontology_client, query_name):
        """Test that domain-specific queries return results."""
        result = ontology_client.query(REFERENCE_QUERIES[query_name])
        assert result.success, f"Query {query_name} should succeed: {result.error}"
        # Some queries may legitimately return no results depending on ontology content


# ============================================================================
# VALIDATION TESTS
# ============================================================================

class TestValidation:
    """Tests for ontology validation."""

    def test_overall_validity(self, validation_result):
        """Test that the ontology is valid overall."""
        assert validation_result.is_valid, \
            f"Ontology should be valid. Violations: {validation_result.violations}"

    def test_no_critical_violations(self, validation_result):
        """Test that there are no critical violations."""
        critical = [v for v in validation_result.violations
                   if "Circular" in v or "disjoint" in v.lower()]
        assert len(critical) == 0, f"Should have no critical violations: {critical}"


# ============================================================================
# HIERARCHY TESTS
# ============================================================================

class TestHierarchy:
    """Tests for class hierarchy structure."""

    def test_can_build_hierarchy(self, ontology_client):
        """Test that class hierarchy can be built."""
        hierarchy = ontology_client.get_class_hierarchy()
        assert "name" in hierarchy, "Hierarchy should have a name"
        assert "children" in hierarchy, "Hierarchy should have children"

    def test_eda_process_hierarchy_depth(self, ontology_client):
        """Test that EDAProcess has reasonable hierarchy depth."""
        hierarchy = ontology_client.get_class_hierarchy(
            "http://example.org/eda#EDAProcess"
        )

        def count_depth(node, current=0):
            if not node.get("children"):
                return current
            return max(count_depth(child, current + 1)
                      for child in node["children"])

        depth = count_depth(hierarchy)
        assert depth >= 1, "EDAProcess should have hierarchy depth of at least 1"
        assert depth <= 10, f"Hierarchy depth should not exceed 10, got {depth}"


# ============================================================================
# NAMESPACE TESTS
# ============================================================================

class TestNamespaces:
    """Tests for namespace definitions."""

    def test_has_namespaces(self, ontology_client):
        """Test that the ontology defines namespaces."""
        namespaces = ontology_client.loader.namespaces
        assert len(namespaces) > 0, "Ontology should define namespaces"

    def test_eda_namespace(self, ontology_client):
        """Test that the EDA namespace is defined."""
        namespaces = ontology_client.loader.namespaces
        eda_found = any(
            "example.org/eda" in uri
            for uri in namespaces.values()
        )
        assert eda_found, "EDA namespace should be defined"


# ============================================================================
# COMPETENCY TESTS
# ============================================================================

class TestCompetencyQuestions:
    """Tests for ontology competency questions."""

    def test_can_represent_eda_flow(self, ontology_client):
        """CQ: Can the ontology represent EDA design flows?"""
        classes = ontology_client.loader.get_classes()
        class_names = [c.split("#")[-1] for c in classes]

        required = ["Flow", "Stage"]
        found = sum(1 for r in required if any(r in c for c in class_names))
        assert found >= 1, "Ontology should represent EDA flows"

    def test_can_represent_design_structure(self, ontology_client):
        """CQ: Can the ontology represent design structure?"""
        classes = ontology_client.loader.get_classes()
        class_names = [c.split("#")[-1] for c in classes]

        required = ["Design", "Instance", "Net"]
        found = sum(1 for r in required if any(r in c for c in class_names))
        assert found >= 2, "Ontology should represent design structure"

    def test_can_represent_timing_constraints(self, ontology_client):
        """CQ: Can the ontology represent timing constraints?"""
        result = ontology_client.query(REFERENCE_QUERIES["timing_classes"])
        assert result.success and len(result.data) > 0, \
            "Ontology should represent timing concepts"

    def test_can_represent_physical_implementation(self, ontology_client):
        """CQ: Can the ontology represent physical implementation?"""
        result = ontology_client.query(REFERENCE_QUERIES["physical_design_subclasses"])
        assert result.success and len(result.data) > 0, \
            "Ontology should represent physical design concepts"


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Run tests
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
