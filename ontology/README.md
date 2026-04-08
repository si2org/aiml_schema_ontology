# Ontology Directory

This directory holds the Si2 ontology release.. The working group ships the ontology together with the ASU/Drexel use cases so that adopters get both the formal semantics and concrete ML workflows.

---

## Files in this folder

- `eda_ontology.ttl`
  - The monolithic Turtle representation of the ontology. It captures the domains called out in the collateral—design entities (`eda:Cell`, `eda:Net`, `eda:Pin`), design flow stages, timing (`timing:TimingPath`, `timing:Constraint`), physical layout (`physical:Layer`, `physical:Polygon`), ML constructs (`ml:LabeledPropertyGraph`, `ml:Dataset`), fab and packaging concepts, plus provenance relationships.
  - Import this file directly into RDFLib, Protégé, or a SPARQL triple store to inspect or extend the classes and object/data properties.

- `eda-ontology-adapter.ttl`
  - A companion ontology that demonstrates the "adapter knowledge graph" pattern described in the collateral. Use it when you need to specialize the base ontology for technology-node rules (e.g., SVRF/DFM). Typical customizations add `rdfs:subClassOf` hierarchies and domain-specific axioms without touching `eda_ontology.ttl`.


Croissant metadata files that map ontology properties to CircuitOps datasets now live under `usecases/ASU/ASU_ML_EDA_data_flow/croissant/` so that the ASU flow owns its data-mapping collateral.

---

## Key domains to explore

Use Protégé or SPARQL to inspect these highlighted areas from the collateral:


### 1. Design Entities
- `eda:Cell`, `eda:Net`, `eda:Pin`, `eda:Port` – fundamental circuit components
- `eda:StandardCell` – library cells with characterized behavior
- `eda:Macro` – hard IP blocks

### 2. Design Flow Stages
- `eda:LogicalSynthesisStage`, `eda:PlacementStage`, `eda:CTSStage`, `eda:RoutingStage`
- Each stage produces specific file formats and analysis results

### 3. Analysis & Metrics
- `eda:TimingAnalysis`, `eda:PowerAnalysis`, `eda:AreaAnalysis`
- Metrics such as `eda:AreaMetric`, `eda:PowerMetric`, `timing:Slack`

### 4. Constraints
- `eda:TimingConstraint`, `eda:AreaConstraint`, `eda:PowerConstraint`
- `timing:Clock` with synchronous/asynchronous relationships

### 5. File Formats
- `eda:CDLFile`, `eda:CPFFile`, `eda:DEFFile`, `eda:SPEFFile`
- Supports tool-agnostic data parsing (e.g., CircuitOps)

### 6. ML Integration
- `ml:Dataset`, `ml:LabeledPropertyGraph`, `eda:CircuitGraph`
- `eda:AgentAction` for agentic workflow primitives

### 7. Advanced Packaging
- `eda:Chiplet`, `eda:Interposer`, `eda:TSV`, `eda:C4Bump`
- Captures 3D integration semantics

### 8. Fabrication
- `eda:Lithography`, `eda:Etch`, `eda:Deposition`
- Front-end/back-end process modules


---

## Working with the ontology

1. **Load into tooling.** Open `eda_ontology.ttl` in Protégé for quick browsing, or use `rdflib.Graph().parse("ontology/eda_ontology.ttl", format="turtle")` as shown inside the ASU data-flow scripts.
2. **Run SPARQL queries.** The SPARQL examples can be executed directly over this TTL file. Examples are showin in [examples](./usecases/ASU/ASU_ML_EDA_data_flow/usecases/examples/.)
3. **Extend responsibly.** Add new classes or properties in a separate adapter file (similar to `eda-ontology-adapter.ttl`) to keep the core ontology stable, then update Croissant metadata to expose new attributes to ML pipelines.
4. **Tie into datasets.** When adding new datasets or extensions to classes to the ontology, keep Croissant metadata in sync so the ASU/Drexel use cases continue to map ontology semantics to real data sources, essentially the regression shouold pass.

## Tests

The `tests/` subdirectory contains the ontology validator, SPARQL query catalog, and pytest suite that originally lived with the MCP bundle. From the repo root run:

```bash
python ontology/tests/run_tests.py --path ontology --main eda_ontology.ttl
pytest ontology/tests/test_eda_ontology.py
```

By default the test runner imports the MCP client from `usecases/MCP`, so keep that directory intact even if you only need the validator.

## How New Users Can Engage

1. **Report Missing Concepts**
   - Open a GitHub issue titled “Ontology lacks representation for [X]”.
   - Include a template with domain, use case, and proposed classes/properties.
   - Ensure the ASU and Drexel usecases pass.

2. **Submit Foundry-Specific Extensions**
   - Contribute adapter ontologies for TSMC, Samsung, Intel, etc.
   - Capture DRC rule semantics derived from PDKs.

3. **Add ML Model Metadata**
   ```ttl
   :arrival_time_predictor a ml:Model ;
       ml:trainedOn :iwls05_dataset ;
       ml:architecture :gcn_6layer ;
       ml:performance [ ml:mae "59.4ps" ] .

4. **Tool Parsers**
    - Contribute adapters for Cadence, Synopsys, Siemens, and other vendor toolchains.
    - Expand file-format coverage (OpenAccess, GDSII, and related semantic extraction pipelines).

---

## Contact

- Ontology maintainer: **Ivan Kissiov** (ivan.kissiov@siemens.com)
- Affiliation: Siemens EDA, Si2 AI/ML Working Group (Chair)
- Use the working-group mailing list or open a GitHub issue for modeling questions.
