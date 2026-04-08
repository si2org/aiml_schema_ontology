# Dataset Generation Scripts

This folder contains core scripts for generating datasets for ML applications using the schema.

## Scripts

- `datagen_json.py`: Utilities to generate datasets using `taxonomy_v0p5.json` (JSON based)
- `datagen_ttl.py`: Utilities to generate datasets using `eda_ontology.ttl` (**RDFLib** based implementation, suitable for generating tabular datasets)
- `datagen_graph.py`: Utilities to generate datasets using `eda_ontology.ttl` (**SPARQL** query based implementation, suitable for graph datasets)
- `server.py`: An example gRPC server script to transfer CSV files
- `data_service.proto`: Proto file to enable gRPC transfer
- `data_service_pb2*.py`: gRPC protobuf files genrated by compiling proto file

---

## Example Usage

### APIs in `datagen_ttl.py` file
The utilities in this file leverages the croissant metadata to identify and read relevant files from the data source.
It then uses RDFLib APIs to filter and join required columns into a unified dataset.
These are well-suited for generating datasets for traditional ML models (e.g., XGBoost, MLP).

### 1. get_graph API
The get_graph function is used to generate a graph-based dataset.
Specify the desired properties for each node type using a dictionary format.

```python
from datagen_ttl import *

# Load schema files
ontology_path = "../../../../ontology/eda_ontology.ttl"
metadata_path = "../croissant/circuitops_croissant_metadata_ontology.json"
graph = load_ontology(ontology_path)
metadata = load_metadata(metadata_path)

# Define features per node type
driver_features = ["pinName", "worstSlew", "libcellName"]
sink_features = ["pinName", "loadCapacitance"]

graph_features = {
    "sourceNode": driver_features,
    "sinkNode": sink_features
}

# Get graph dataset
dataset = get_graph(graph, EDA.TimingGraph, graph_features, metadata)
```

---

### 2. get_properties_dataset API
The get_properties_dataset function is used to get properties of a specific entity.
Pass the required properties as a list.

```python
from datagen_ttl import *

# Load schema files
ontology_path = "../../../../ontology/eda_ontology.ttl"
metadata_path = "../croissant/circuitops_croissant_metadata_ontology.json"
graph = load_ontology(ontology_path)
metadata = load_metadata(metadata_path)

# Define properties for a specific class (e.g., Pin)
features = ["pinName", "worstSlew", "libcellName"]
pin_props_dataset = get_properties_dataset(graph, metadata, EDA.Pin, features)
```

---
### APIs in `datagen_graph.py` file
The utilities in this file constructs an ontology-driven knowledge graph by loading data using the croissant file.
It then employs SPARQL queries for graph-based data processing and feature extraction.
This is ideal for GNN-based ML models.

### 1. convert_croissant_to_rdf API
The convert_croissant_to_rdf fucntion is used to create an instance of the ontology graph with the values from the data source incorporated.
Once the data source is converted into a RDF based knowledge graph, user can employ SPARQL queries on it and manipulate the EDA data.
An example script on how to use SPARQL queries is given at [SPARQL_query_examples.py](../usecases/examples/SPARQL_query_examples.py)

```python
from datagen_graph import *

# Load schema files
ontology_path = "../../../../ontology/eda_ontology.ttl"
metadata_path = "../croissant/circuitops_croissant_metadata_ontology.json"
graph = load_ontology(ontology_path)
metadata = load_metadata(metadata_path)

# Convert the Croissant metadata into an RDF graph
graph = convert_croissant_to_rdf(metadata, graph)
```

### 2. get_filtered_rdf_graph API
The get_filtered_rdf_graph function is used to generate an instance of ontology graph only with given properties.
Specify the desired properties in a list format.

```python
from datagen_graph import *

# Load schema files
ontology_path = "../../../../ontology/eda_ontology.ttl"
metadata_path = "../croissant/circuitops_croissant_metadata_ontology.json"
graph = load_ontology(ontology_path)
metadata = load_metadata(metadata_path)

# Convert the Croissant metadata into an RDF graph
graph = convert_croissant_to_rdf(metadata, graph)
    
properties = ["pinName", "loadCapacitance", "netCapacitance", "netLength", "setupRiseArrival", "setupFallArrival", "pinX", "pinY"]

# get filtered RDF graph using get_filtered_rdf_graph API. Uses SPARQL query under the hood.
filtered_graph = get_filtered_rdf_graph(properties, graph)

```

## Notes

- These utilities depend on the schema definitions provided in the `ontology/` directory, so the property names must align with the schema terminology
- Datasets are generated based on the Croissant mapping file. Be sure to use the version that corresponds to your specific data source.
- Use these functions as building blocks to create schema-consistent ML datasets from EDA designs.

Refer to the [usecases](../usecases/) directory for examples on how to integrate these APIs into ML applications.

