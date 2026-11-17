#!/usr/bin/env python3
"""
Regression tests for the "process" terminology cleanup.

See ontology/docs/process-terminology.md. These tests guard that:
  * computational EDA processes and semiconductor manufacturing steps are disjoint
    siblings under eda:Activity, and stay so under OWL-RL reasoning;
  * final-layout files feed a computational handoff step (MaskDataPreparation),
    not a fabrication step;
  * process technology is a first-class concept linked to corners, operating
    conditions, libraries and manufacturing steps;
  * the redundant string properties eda:process / eda:processCorner are deprecated
    in favour of eda:processFactor and eda:hasProcessCorner;
  * a ProcessCorner is no longer inferred to be an OperatingCondition, and
    hasOperatingCondition / hasRCCorner each have a single rdfs:domain.
"""

from pathlib import Path

import pytest
import rdflib
from rdflib import Namespace, RDF, RDFS, OWL, Literal

import owlrl  # required (ontology/requirements.txt); fail rather than silently skip

ONTOLOGY_FILE = Path(__file__).resolve().parents[1] / "eda_ontology.ttl"
EDA = Namespace("http://example.org/eda#")
DCT = Namespace("http://purl.org/dc/terms/")
EX = Namespace("http://example.org/test#")
ERROR = rdflib.URIRef("http://www.daml.org/2002/03/agents/agent-ont#error")


@pytest.fixture(scope="module")
def tbox():
    g = rdflib.Graph()
    g.parse(ONTOLOGY_FILE, format="turtle")
    return g


def _reason(graph, extra_triples=()):
    g = rdflib.Graph()
    for t in graph:
        g.add(t)
    for t in extra_triples:
        g.add(t)
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
    return g


@pytest.fixture(scope="module")
def closure(tbox):
    return _reason(tbox)


def _manufacturing_classes(g):
    return {
        c for c in g.transitive_subjects(RDFS.subClassOf, EDA.SemiconductorManufacturingProcess)
        if c != OWL.Nothing
    }


def _errors(g):
    return [str(o) for o in g.objects(None, ERROR)]


# ---------------------------------------------------------------------------
# 1. Computing vs. manufacturing processes
# ---------------------------------------------------------------------------

class TestProcessHierarchySplit:

    def test_activity_is_common_parent(self, tbox):
        assert (EDA.EDAProcess, RDFS.subClassOf, EDA.Activity) in tbox
        assert (EDA.SemiconductorManufacturingProcess, RDFS.subClassOf, EDA.Activity) in tbox

    def test_manufacturing_not_asserted_under_eda_process(self, tbox):
        assert (EDA.SemiconductorManufacturingProcess, RDFS.subClassOf, EDA.EDAProcess) not in tbox

    def test_disjoint(self, tbox):
        assert (EDA.SemiconductorManufacturingProcess, OWL.disjointWith, EDA.EDAProcess) in tbox

    def test_no_manufacturing_class_inferred_under_eda_process(self, closure):
        mfg = _manufacturing_classes(closure)
        assert EDA.Doping in mfg and EDA.Patterning in mfg
        leaked = sorted(str(c) for c in mfg if (c, RDFS.subClassOf, EDA.EDAProcess) in closure)
        assert not leaked, f"Manufacturing classes inferred to be EDA processes: {leaked}"

    def test_no_manufacturing_class_punned_as_eda_process(self, closure):
        # Class-level property values (e.g. `eda:GDSIIFile eda:isInputTo eda:Patterning`)
        # type the object via the property range; this must not hit manufacturing classes.
        mfg = _manufacturing_classes(closure)
        leaked = sorted(str(c) for c in mfg if (c, RDF.type, EDA.EDAProcess) in closure)
        assert not leaked, f"Manufacturing classes typed as eda:EDAProcess: {leaked}"

    def test_ontology_consistent(self, closure):
        assert not _errors(closure), _errors(closure)

    def test_disjointness_is_enforced(self, tbox):
        g = _reason(tbox, [
            (EX.step, RDF.type, EDA.Doping),
            (EX.step, RDF.type, EDA.LogicalSynthesis),
        ])
        assert any("Disjoint" in e for e in _errors(g))

    def test_shared_activity_properties(self, tbox):
        for prop in (EDA.precedes, EDA.hasSubProcess, EDA.isPartOf):
            assert (prop, RDFS.domain, EDA.Activity) in tbox, prop
            assert (prop, RDFS.range, EDA.Activity) in tbox, prop

    def test_data_flow_properties_stay_on_eda_process(self, tbox):
        for prop in (EDA.consumes, EDA.produces, EDA.usesTool):
            assert (prop, RDFS.domain, EDA.EDAProcess) in tbox, prop
        for prop in (EDA.isInputTo, EDA.isOutputOf):
            assert (prop, RDFS.range, EDA.EDAProcess) in tbox, prop

    def test_manufacturing_sequence_is_consistent(self, tbox):
        g = _reason(tbox, [
            (EX.dep, RDF.type, EDA.FilmFormation),
            (EX.litho, RDF.type, EDA.Patterning),
            (EX.dep, EDA.precedes, EX.litho),
        ])
        assert not _errors(g), _errors(g)
        assert (EX.litho, RDF.type, EDA.EDAProcess) not in g


# ---------------------------------------------------------------------------
# 2. Design-to-manufacturing handoff (GDSII / OASIS)
# ---------------------------------------------------------------------------

class TestLayoutHandoff:

    def test_mask_data_preparation_is_eda_process(self, tbox):
        assert (EDA.MaskDataPreparation, RDFS.subClassOf, EDA.EDAProcess) in tbox

    @pytest.mark.parametrize("fmt", [EDA.GDSIIFile, EDA.OASISFile])
    def test_layout_not_input_to_fabrication(self, tbox, fmt):
        assert (fmt, EDA.isInputTo, EDA.Patterning) not in tbox
        assert (fmt, EDA.isInputTo, EDA.MaskDataPreparation) in tbox

    def test_gds_instance_flow_has_no_process_clash(self, tbox):
        # Only process-related clashes are checked. A GDSIIFile instance used with
        # isInputTo also hits a pre-existing, unrelated clash (isInputTo has domain
        # FileFormat, GDSIIFile is a Layout, FileFormat is disjoint with Layout);
        # see "Out of scope" in docs/process-terminology.md.
        g = _reason(tbox, [
            (EX.gds, RDF.type, EDA.GDSIIFile),
            (EX.mdp, RDF.type, EDA.MaskDataPreparation),
            (EX.gds, EDA.isInputTo, EX.mdp),
            (EX.litho, RDF.type, EDA.Patterning),
            (EX.mdp, EDA.precedes, EX.litho),
        ])
        process_terms = ("EDAProcess", "SemiconductorManufacturingProcess", "Activity",
                         "ProcessTechnology")
        clashes = [e for e in _errors(g) if any(t in e for t in process_terms)]
        assert not clashes, clashes
        assert (EX.litho, RDF.type, EDA.EDAProcess) not in g


# ---------------------------------------------------------------------------
# 3. Process technology
# ---------------------------------------------------------------------------

class TestProcessTechnology:

    def test_class_exists(self, tbox):
        assert (EDA.ProcessTechnology, RDF.type, OWL.Class) in tbox

    @pytest.mark.parametrize("prop,domain,range_", [
        (EDA.realizedBy, EDA.ProcessTechnology, EDA.SemiconductorManufacturingProcess),
        (EDA.cornerOfTechnology, EDA.ProcessCorner, EDA.ProcessTechnology),
        (EDA.describesTechnology, EDA.TechnologyArtifact, EDA.ProcessTechnology),
    ])
    def test_simple_links(self, tbox, prop, domain, range_):
        assert (prop, RDF.type, OWL.ObjectProperty) in tbox
        assert (prop, RDFS.domain, domain) in tbox
        assert (prop, RDFS.range, range_) in tbox

    def test_operating_condition_links_to_technology(self, tbox):
        assert (EDA.characterizedForTechnology, RDFS.range, EDA.ProcessTechnology) in tbox
        g = _reason(tbox, [
            (EX.n5, RDF.type, EDA.ProcessTechnology),
            (EX.tt, RDF.type, EDA.ProcessCorner),
            (EX.tt, EDA.name, Literal("TT")),
            (EX.tt, EDA.cornerOfTechnology, EX.n5),
            (EX.oc, RDF.type, EDA.OperatingCondition),
            (EX.oc, EDA.characterizedForTechnology, EX.n5),
            (EX.oc, EDA.hasProcessCorner, EX.tt),
            (EX.oc, EDA.processFactor, Literal(1.0, datatype=rdflib.XSD.double)),
        ])
        assert not _errors(g), _errors(g)


# ---------------------------------------------------------------------------
# 4. Process corner properties
# ---------------------------------------------------------------------------

class TestProcessCornerProperties:

    @pytest.mark.parametrize("prop,replacement", [
        (EDA.process, EDA.processFactor),
        (EDA.process, EDA.hasProcessCorner),
        (EDA.processCorner, EDA.hasProcessCorner),
    ])
    def test_deprecated_with_replacement(self, tbox, prop, replacement):
        assert (prop, OWL.deprecated, Literal(True)) in tbox
        assert (prop, DCT.isReplacedBy, replacement) in tbox

    def test_deprecated_properties_documented(self, tbox):
        for prop in (EDA.process, EDA.processCorner):
            assert list(tbox.objects(prop, RDFS.label)), prop
            assert list(tbox.objects(prop, RDFS.comment)), prop

    def test_process_factor_numeric(self, tbox):
        assert (EDA.processFactor, RDFS.range, rdflib.XSD.double) in tbox
        assert (EDA.nomProcess, RDFS.range, rdflib.XSD.double) in tbox

    def test_process_corner_not_inferred_operating_condition(self, tbox):
        g = _reason(tbox, [
            (EX.av, RDF.type, EDA.AnalysisView),
            (EX.av, EDA.hasProcessCorner, EX.ss),
            (EX.av, EDA.hasVoltageCorner, EX.v),
            (EX.av, EDA.hasTemperatureCorner, EX.t),
        ])
        for corner in (EX.ss, EX.v, EX.t):
            assert (corner, RDF.type, EDA.OperatingCondition) not in g, corner
        assert (EX.ss, RDF.type, EDA.Corner) in g

    @pytest.mark.parametrize("prop", [EDA.hasOperatingCondition, EDA.hasRCCorner])
    def test_single_domain(self, tbox, prop):
        domains = list(tbox.objects(prop, RDFS.domain))
        assert len(domains) == 1, f"{prop} has {len(domains)} rdfs:domain statements"


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
