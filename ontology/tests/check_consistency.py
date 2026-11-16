#!/usr/bin/env python3
"""
OWL-RL consistency check for the EDA ontology.

Loads one or more Turtle files, computes the OWL-RL closure with owlrl, and reports
every inconsistency owlrl detects (e.g. an individual in two disjoint classes).
Exits 1 if any inconsistency is found, 0 otherwise.

    python ontology/tests/check_consistency.py ontology/eda_ontology.ttl [more.ttl ...]
"""

import argparse
import sys

import rdflib
from rdflib import RDF, RDFS, OWL

try:
    import owlrl
except ImportError:  # pragma: no cover
    sys.exit(f"owlrl is not installed for {sys.executable}.\n"
             "Run 'make install' (or: pip install -r ontology/requirements.txt).")

ERROR = rdflib.URIRef("http://www.daml.org/2002/03/agents/agent-ont#error")
EDA = rdflib.Namespace("http://example.org/eda#")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("files", nargs="+", help="Turtle files to load together")
    args = parser.parse_args()

    g = rdflib.Graph()
    for path in args.files:
        g.parse(path, format="turtle")
    asserted = len(g)

    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)

    errors = sorted(str(o) for o in g.objects(None, ERROR))
    unsatisfiable = sorted(
        str(c) for c in g.subjects(OWL.equivalentClass, OWL.Nothing)
        if isinstance(c, rdflib.URIRef) and c != OWL.Nothing
    )

    print(f"Loaded {', '.join(args.files)}: {asserted} asserted triples, "
          f"{len(g)} after OWL-RL closure")

    # Guard for the process-terminology split (docs/process-terminology.md).
    leaked = sorted(
        str(c) for c in g.transitive_subjects(RDFS.subClassOf, EDA.SemiconductorManufacturingProcess)
        if c != OWL.Nothing and ((c, RDFS.subClassOf, EDA.EDAProcess) in g
                                 or (c, RDF.type, EDA.EDAProcess) in g)
    )

    for msg in errors:
        print(f"INCONSISTENT: {msg}")
    for cls in unsatisfiable:
        print(f"UNSATISFIABLE: {cls}")
    for cls in leaked:
        print(f"PROCESS-SPLIT: manufacturing class inferred as eda:EDAProcess: {cls}")

    if errors or unsatisfiable or leaked:
        return 1
    print("OK: no inconsistencies detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
