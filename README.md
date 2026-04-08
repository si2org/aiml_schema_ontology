# Si2 AI/ML Schema Ontology Repository

This repo captures the Si2 AI/ML schema working group’s release: a monolithic EDA ontology plus three first-class use cases (MCP, ASU, Drexel) that demonstrate how to apply it. Each directory is self-contained with adjacently located documentation and tests so you can stand up the ontology and its use cases without hunting for collateral elsewhere.

- `ontology/` publishes the canonical OWL/Turtle definitions and ontology-level tests.
- `usecases/MCP/` shows how to expose the ontology via a Model Context Protocol (MCP) server for agentic flows.
- `usecases/ASU/ASU_ML_EDA_data_flow/` implements the CircuitOps-inspired Croissant + ontology data pipeline used for timing ML.
- `usecases/Drexel/` mirrors the Drexel EDA-ML tasks for graph-learning.

**Purpose of the ontology and release**
- Provide a single, well-documented OWL/Turtle ontology (`ontology/`) that encodes EDA entities, flow stages, constraints, metrics, and metadata so ML pipelines can understand “what” design data means rather than just file schemas.
- Supply three concrete use cases that lock the ontology abstraction to practical workflows:
  1. **MCP** – demonstrate how an MCP server/client can expose ontology semantics to agents, SPARQL queries, and LLM tools.
  2. **ASU** – show how Croissant + ontology mappings generate timing datasets from CircuitOps CSVs and feed ML models.
  3. **Drexel** – mirror the Drexel EDA-ML graphs to illustrate graph learning with ontology-backed semantics.
These use cases are part of the release so you can reproduce the exact flows used by the working group and extend them for your own data.

The EDA ontology provides a semantic foundation for AI-driven EDA, addressing the fundamental challenge that schema-based representations fail to capture: machines need semantic understanding, not just structural access.


**Core value proposition**
- Enables autonomous agents to discover, compose, and reason about EDA workflows
- Bridges graph representations, ML datasets, and tool semantics through RDF/OWL formalism
- Proven on production-scale industrial use cases (NVIDIA CircuitOps, Drexel EDA-ML)

**Target audience**
- ML researchers
- EDA tool developers
- Design-automation engineers
- Semiconductor process engineers

---

## Repository layout

```
.
├── ontology/                       # OWL/Turtle ontology definitions and adapter files
├── usecases/
│   ├── MCP/                        # MCP server/client reference use case 
│   ├── ASU/ASU_ML_EDA_data_flow/   # CircuitOps-inspired data flow, designs, Croissant-driven scripts, pytest suite
│   └── Drexel/                     # Drexel EDA-ML artifacts 
└── README.md                       # Top-level orientation
```

---

## What lives where

- `ontology/`
  - `eda_ontology.ttl` and `eda-ontology-adapter.ttl` capture the monolithic ontology referenced throughout the repo.
  - Use these files directly, or split them into modular namespaces (timing, physical, ML, DFM, etc.) when you need a smaller import surface.
- `usecases/ASU/ASU_ML_EDA_data_flow/`
  - Implements the CircuitOps-style flow: convert DEF/LEF/SPEF/LIB into labeled property graphs (LPGs) and generate datasets via Croissant metadata (`scripts/`).
  - Contains Python tooling (`src/`), the `croissant/` folder holding `circuitops_croissant_metadata_ontology.json`, CircuitOps sample designs, and ML demos under `usecases/`.  See its [README](./usecases/ASU/ASU_ML_EDA_data_flow/README.md) for setup commands.
- `usecases/MCP/`
  - Treats the MCP server/client as another use case. Spin up the Model Context Protocol endpoint, exercise the SPARQL catalog to show how an LLM would interact with the ontology.
- `usecases/Drexel/`
  - Hosts the Drexel EDA-ML framework artifacts: graph construction code, feature taxonomies, and notebooks that mirror the ICCAD publication cited in the collateral.
---


## Why ontology + Croissant?

- Ontology captures semantics (relationships, hierarchy, provenance) that schemas alone cannot—critical for agent workflows, explainability, and cross-domain inference. Example SPARQL from the PDF demonstrates reasoning across timing + DRC using shared `:location` properties.
- Croissant metadata declares ML datasets in a machine-actionable way (splits, feature types, licensing). Together, they bridge human-readable ontology classes with the tabular/graph data you actually train on.
- The collateral outlines falsifiable claims (faster data discovery, fewer breaking changes, fewer hallucinations) that you can measure as you adopt the ontology.

---

## Getting oriented

1. **Explore `ontology/`.** Start with `eda_ontology.ttl`, then open `eda-ontology-adapter.ttl` if you need the SVRF/DFM extensions described under "Adapter Knowledge Graphs". Use [Protégé](https://protege.stanford.edu/) or RDFLib to inspect classes such as `eda:Cell`, `timing:TimingPath`, and `ml:LabeledPropertyGraph`.
2. **Run the ASU data flow.** Follow `usecases/ASU/ASU_ML_EDA_data_flow/README.md` to install requirements, generate datasets from the provided CircuitOps CSV tables using the mapping files also , and execute the pytest suite.
3. **Run the Drexel data flow.** The `usecases/Drexel` folder mirrors the "EDA-ML Feature Mapping" section: it shows how to build timing path graphs (TPG) and interconnect graphs (IG) with the 24 standardized features.
4. **Spin up the MCP use case.** `usecases/MCP/` packages the Model Context Protocol server, client, and SPARQL cookbook so you can expose the ontology as an MCP endpoint. Follow its [README]() to start the server (`python server.py --file ../../ontology/eda_ontology.ttl`) and try the client/demo queries.

---


For detailed implementation notes and API references see the README files inside each directory. Contributions should keep the ontology authoritative, keep the ASU/Drexel use cases reproducible by running the CI, and update the release collateral as the project evolves.
