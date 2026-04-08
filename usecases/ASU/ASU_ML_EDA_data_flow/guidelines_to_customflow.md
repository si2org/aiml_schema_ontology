# Guidelines to Customize the Data Generation Flow

This file provides instructions for adapting the data generation framework to your own ML application, data sources, or infrastructure.

Refer to the scripts in example [usecases]('./usecases/') and modify the required parts.
---

## For Custom ML Applications

If you're working on a new ML use case, you can specify different features or labels by changing the input to the data generation APIs:

- Update the `graph_features` dictionary in your script to match the properties required from each node type.
- Or, if using `get_properties_dataset`, adjust the list of properties accordingly.

---

## For Custom Data Sources

To use your own CSV or other structured files:

- Provide a new Croissant file in `croissant/` (e.g., replace `croissant/circuitops_croissant_metadata_ontology.json`). 
- The new Corissant file has to map each schema-defined property to the correct file and column in your dataset.
- Ensure file names and column names in the metadata match those in your data.

---

## For Custom Server Setup

If you're deploying the framework in a distributed setting:

- Edit the gRPC schema in `data_service.proto` to support new file types or services.
- Regenerate the `*_pb2.py` and `*_pb2_grpc.py` files using:
  ```bash
  python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. data_service.proto
  ```
