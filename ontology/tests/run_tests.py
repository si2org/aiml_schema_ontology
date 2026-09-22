#!/usr/bin/env python3
"""
EDA Ontology Test Runner for Monolithic Architecture

This script provides a comprehensive test runner for the monolithic EDA ontology,
including validation, SPARQL query testing, and report generation.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict

CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parents[1]
MCP_DIR = REPO_ROOT / "usecases" / "MCP"
DEFAULT_ONTOLOGY_DIR = REPO_ROOT / "ontology"
if str(MCP_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_DIR))

sys.path.insert(0, str(CURRENT_DIR))

from mcp_client import MCPOntologyClient, MonolithicOntologyLoader, REFERENCE_QUERIES  # type: ignore
from ontology_validator import validate_ontology, EDAOntologyValidator  # type: ignore
from sparql_queries import ALL_QUERIES, get_queries_by_domain, get_all_domains  # type: ignore


@dataclass
class TestResult:
    """Container for test results"""
    name: str
    passed: bool
    message: str
    duration: float = 0.0
    details: Dict[str, Any] = None


class OntologyTestRunner:
    """
    Comprehensive test runner for the monolithic EDA ontology.
    Runs validation, query tests, and generates reports.
    """

    def __init__(self, ontology_path: str = str(DEFAULT_ONTOLOGY_DIR),
                 main_file: str = "eda_ontology.ttl",
                 adapter_file: str = None):
        self.ontology_path = ontology_path
        self.main_file = main_file
        self.adapter_file = adapter_file
        self.client = MCPOntologyClient(ontology_path)
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None

    def initialize(self) -> bool:
        """Initialize the test runner"""
        success, message = self.client.initialize(self.main_file, self.adapter_file)
        if not success:
            print(f"Failed to initialize: {message}")
            return False
        return True

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test categories"""
        self.start_time = time.time()
        self.results = []

        print("=" * 70)
        print("MONOLITHIC EDA ONTOLOGY TEST RUNNER")
        print("=" * 70)
        print(f"\nOntology: {self.ontology_path}/{self.main_file}")
        if self.adapter_file:
            print(f"Adapter:  {self.ontology_path}/{self.adapter_file}")

        # Initialize
        print("\n[1/5] Initializing...")
        if not self.initialize():
            return self._generate_summary()

        stats = self.client.get_stats()
        print(f"      Loaded {stats['triple_count']} triples from {stats['file_count']} files")

        # Run test categories
        print("\n[2/5] Running file integrity tests...")
        self._run_file_integrity_tests()

        print("\n[3/5] Running validation tests...")
        self._run_validation_tests()

        print("\n[4/5] Running SPARQL query tests...")
        self._run_query_tests()

        print("\n[5/5] Running competency tests...")
        self._run_competency_tests()

        self.end_time = time.time()

        return self._generate_summary()

    def _run_file_integrity_tests(self):
        """Run file integrity tests"""
        expected_files = ["eda_ontology.ttl"]
        if self.adapter_file:
            expected_files.append(self.adapter_file)

        for filename in expected_files:
            start = time.time()
            path = os.path.join(self.ontology_path, filename)
            exists = os.path.exists(path)

            self.results.append(TestResult(
                name=f"file_exists_{filename}",
                passed=exists,
                message=f"File {'exists' if exists else 'NOT FOUND'}: {filename}",
                duration=time.time() - start
            ))

            status = "PASS" if exists else "FAIL"
            print(f"      [{status}] {filename}")

    def _run_validation_tests(self):
        """Run validation tests"""
        start = time.time()

        validator = EDAOntologyValidator(self.ontology_path)
        if not validator.load_ontology(self.main_file, self.adapter_file):
            self.results.append(TestResult(
                name="validation_load",
                passed=False,
                message="Failed to load ontology for validation",
                duration=time.time() - start
            ))
            print("      [FAIL] Failed to load ontology")
            return

        report = validator.validate()

        # Add validation result
        self.results.append(TestResult(
            name="syntax_validation",
            passed=report.syntax_valid,
            message="Syntax validation " + ("passed" if report.syntax_valid else "failed"),
            duration=time.time() - start,
            details={"metrics": asdict(report.metrics)}
        ))
        status = "PASS" if report.syntax_valid else "FAIL"
        print(f"      [{status}] Syntax validation")

        self.results.append(TestResult(
            name="semantic_validation",
            passed=report.semantic_valid,
            message="Semantic validation " + ("passed" if report.semantic_valid else "failed"),
            duration=time.time() - start
        ))
        status = "PASS" if report.semantic_valid else "FAIL"
        print(f"      [{status}] Semantic validation")

        # Check for critical errors
        critical_errors = [i for i in report.issues if i.severity == "error"]
        has_no_errors = len(critical_errors) == 0

        self.results.append(TestResult(
            name="no_critical_errors",
            passed=has_no_errors,
            message=f"Critical errors: {len(critical_errors)}",
            duration=time.time() - start,
            details={"errors": [i.message for i in critical_errors[:5]]}
        ))
        status = "PASS" if has_no_errors else "FAIL"
        print(f"      [{status}] No critical errors ({len(critical_errors)} found)")

        # Print metrics
        m = report.metrics
        print(f"\n      Metrics:")
        print(f"        Triples: {m.total_triples}")
        print(f"        Classes: {m.class_count}")
        print(f"        Object Properties: {m.object_property_count}")
        print(f"        Datatype Properties: {m.datatype_property_count}")
        print(f"        Disjoint Axioms: {m.disjoint_axiom_count}")

    def _run_query_tests(self):
        """Run SPARQL query tests"""
        domains = get_all_domains()
        total_passed = 0
        total_failed = 0

        for domain in sorted(domains):
            queries = get_queries_by_domain(domain)
            domain_passed = 0
            domain_failed = 0

            for query in queries:
                start = time.time()
                result = self.client.query(query.query)
                duration = time.time() - start

                # Check success and minimum results
                passed = result.success and len(result.data) >= query.expected_min_results

                self.results.append(TestResult(
                    name=f"query_{query.name}",
                    passed=passed,
                    message=f"Query '{query.name}': {len(result.data)} results" if result.success else f"Query failed: {result.error}",
                    duration=duration,
                    details={
                        "domain": domain,
                        "result_count": len(result.data),
                        "expected_min": query.expected_min_results
                    }
                ))

                if passed:
                    domain_passed += 1
                    total_passed += 1
                else:
                    domain_failed += 1
                    total_failed += 1

            status = "PASS" if domain_failed == 0 else "WARN" if domain_passed > 0 else "FAIL"
            print(f"      [{status}] {domain}: {domain_passed}/{len(queries)} queries passed")

        print(f"\n      Total: {total_passed} passed, {total_failed} failed")

    def _run_competency_tests(self):
        """Run ontology competency tests"""
        classes = self.client.loader.get_classes()
        props = self.client.loader.get_properties()

        competency_tests = [
            ("can_represent_eda_flow", ["Flow", "Stage", "EDAProcess"]),
            ("can_represent_design_structure", ["Design", "Instance", "Net", "Pin"]),
            ("can_represent_timing", ["Timing", "Clock", "Path"]),
            ("can_represent_physical_design", ["Placement", "Routing", "PhysicalDesign"]),
            ("can_represent_verification", ["Verification", "Simulation"]),
            ("can_represent_file_formats", ["LEF", "DEF", "File"]),
            ("can_represent_multi_chiplet", ["Chiplet", "Interposer"]),
            ("can_represent_library", ["Library", "LibCell"])
        ]

        for test_name, required in competency_tests:
            start = time.time()
            passed = all(any(req in c for c in classes) for req in required)

            self.results.append(TestResult(
                name=test_name,
                passed=passed,
                message=f"Competency test: {test_name}",
                duration=time.time() - start,
                details={"required": required}
            ))

            status = "PASS" if passed else "FAIL"
            print(f"      [{status}] {test_name}")

        # Check for key properties
        prop_tests = [
            ("has_consumes_produces", ["consumes", "produces"]),
            ("has_design_structure_props", ["hasInstance", "hasNet", "hasPort"])
        ]

        for test_name, required in prop_tests:
            start = time.time()
            all_props = props["object"]
            passed = all(any(req in p for p in all_props) for req in required)

            self.results.append(TestResult(
                name=test_name,
                passed=passed,
                message=f"Property test: {test_name}",
                duration=time.time() - start,
                details={"required": required}
            ))

            status = "PASS" if passed else "FAIL"
            print(f"      [{status}] {test_name}")

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test summary"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        total_duration = (self.end_time or time.time()) - (self.start_time or time.time())

        # Group by category
        categories = {}
        for result in self.results:
            category = result.name.split("_")[0]
            if category not in categories:
                categories[category] = {"passed": 0, "failed": 0}
            if result.passed:
                categories[category]["passed"] += 1
            else:
                categories[category]["failed"] += 1

        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "duration_seconds": total_duration,
            "categories": categories,
            "results": [asdict(r) for r in self.results]
        }

        return summary

    def print_summary(self, summary: Dict[str, Any]):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"\nTotal Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Duration: {summary['duration_seconds']:.2f}s")

        print("\nBy Category:")
        for category, counts in sorted(summary["categories"].items()):
            total = counts["passed"] + counts["failed"]
            print(f"  {category}: {counts['passed']}/{total}")

        if summary["failed"] > 0:
            print("\nFailed Tests:")
            for result in summary["results"]:
                if not result["passed"]:
                    print(f"  - {result['name']}: {result['message']}")

        print("\n" + "=" * 70)

        return summary["failed"] == 0


def run_pytest():
    """Run pytest test suite"""
    import subprocess
    print("\nRunning pytest test suite...")
    result = subprocess.run(
        ["python", "-m", "pytest", "test_eda_ontology.py", "-v", "--tb=short"],
        capture_output=False
    )
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Monolithic EDA Ontology Test Runner")
    parser.add_argument("--path", default=str(DEFAULT_ONTOLOGY_DIR), help="Path to ontology directory")
    parser.add_argument("--main", default="eda_ontology.ttl", help="Main ontology file")
    parser.add_argument("--adapter", default=None, help="Adapter ontology file")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--pytest", action="store_true", help="Also run pytest suite")
    parser.add_argument("--query-only", action="store_true", help="Run only query tests")
    parser.add_argument("--validate-only", action="store_true", help="Run only validation")
    args = parser.parse_args()

    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    runner = OntologyTestRunner(args.path, args.main, args.adapter)

    if args.validate_only:
        is_valid, report_text, report = validate_ontology(args.path, args.main, args.adapter)
        print(report_text)
        return 0 if is_valid else 1

    if args.query_only:
        if not runner.initialize():
            return 1
        runner._run_query_tests()
        return 0

    summary = runner.run_all_tests()

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        success = runner.print_summary(summary)

    if args.pytest:
        pytest_success = run_pytest()
        if not pytest_success:
            return 1

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
