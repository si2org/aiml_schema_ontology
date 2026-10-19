# AIML_Schema_Ontology

This repository contains tools and utilities for working with Electronic Design Automation (EDA) schemas, ontologies, and related data formats. It provides tools for converting between different data formats and for analyzing EDA data using machine learning techniques.

## Project Structure

- `ontology/`: Core Python modules for working with EDA schemas and ontologies
  - `eda_schema_ontology.py`: Core utilities for ontology manipulation and graph building
  - `DXLTables.py`: Conversion utility for graph JSON files to CSV format
  - `DXLCroissant.py`: Handler for Croissant metadata for EDA schemas
  - `eda-ontology-final.ttl`: The final EDA ontology in Turtle format
  - `eda-ontology.png`: Visualization of the ontology structure
- `usecases/`: Example applications and use cases
  - `length_prediction`: Neural network for predicting net lengths
  - `timing_prediction`: Graph neural network for predicting timing characteristics
- `schema/`: Schema definitions and taxonomies
  - `circuitops_croissant_metadata.json`: Croissant schema metadata
  - `eda_ontology.ttl`: EDA ontology in Turtle format
  - `taxonomy_v0p5.json`: Taxonomy definitions
- `eda_schema/`: Core EDA schema package
  - Utils and base modules for schema handling
- `eda_schema_samples/`: Sample data for testing and demonstration
  - Contains CSV, JSON data samples and design files
- `ASU_flow_scripts/`: Scripts for ASU flow integration
  - Contains designs and source files
- Shell scripts:
  - `graphs_to_csv.sh`: Wrapper script for DXLTables.py to convert graph JSON to CSV
  - `tables_to_croissant.sh`: Wrapper script for DXLCroissant.py to convert tables to Croissant

## Getting Started

1. Clone this repository
2. Create a virtual environment and install the dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-ml.txt
```
3. Use the provided shell scripts for common tasks:
```bash
# Convert graph JSON files to CSV format
./util_scripts/graphs_to_csv.sh -h  # View help options
./util_scripts/graphs_to_csv.sh -a  # Process all graph directories

# Convert CSV tables to Croissant metadata
./util_scripts/tables_to_croissant.sh -h  # View help options
./util_scripts/tables_to_croissant.sh -c combined_croissant_metadata.json  # Create combined metadata
```

4. Run the example scripts from the project root:
```bash
# For neural network-based net length prediction
python usecases/length_prediction/main.py

# For graph neural network-based timing prediction
python usecases/timing_prediction/main.py
```

## Core Modules and Utilities

### ontology/eda_schema_ontology.py

The core module for working with EDA ontologies and building graph-based representations of electronic design data. Key features:

- Load and explore ontology files in Turtle (.ttl) format
- Extract class properties and relationships
- Build and visualize the ontology structure
- Load Croissant metadata into pandas DataFrames
- Construct NetworkX graph representations from design data
- Query ontology entities and their properties

For detailed usage examples, see the [EDA Schema Ontology section in usage_examples.md](usage_examples.md#eda-schema-ontology---core-utilities).

### ontology/DXLTables.py and ontology/DXLCroissant.py

These modules provide functionality for converting between different data formats:

- `DXLTables.py`: Converts graph JSON files to CSV format with metadata columns
- `DXLCroissant.py`: Handles Croissant metadata for EDA schemas and converts CSV tables to Croissant JSON

Shell wrapper scripts are provided to simplify the usage of these tools:
- `graphs_to_csv.sh`: Wrapper for DXLTables.py
- `tables_to_croissant.sh`: Wrapper for DXLCroissant.py

### Example Use Cases

The repository includes machine learning models that demonstrate applications of the EDA schema ontology:

- `length_prediction/main.py`: Neural network for predicting net wire lengths after routing based on pre-routing features
- `timing_prediction/main.py`: Graph Neural Network (GNN) models for predicting timing characteristics

For detailed explanations of these models, see the [Machine Learning Use Cases](usage_examples.md#machine-learning-use-cases) section in the user guide.


## Test Suite & Regression Testing

This project includes a set of automated regression tests to ensure the ML pipelines and ontology-processing workflows remain stable and reproducible across updates.

### Test Location

All pytest tests live in:

```
drexel_ice/tests/
```

These tests run the end-to-end pipelines inside the `usecases/` directory and verify their outputs.

---

### Golden Files

Each use case writes its output CSVs into a local `results/` folder.  
The test suite compares these outputs against checked-in golden reference files.

#### **Length Prediction**
```
drexel_ice/usecases/length_prediction/results/results.csv.golden
```

#### **Timing Prediction (GNN Models)**  
Golden files:

```
drexel_ice/usecases/timing_prediction/results/arrival_time.csv.golden
drexel_ice/usecases/timing_prediction/results/required_time.csv.golden
drexel_ice/usecases/timing_prediction/results/slack.csv.golden
```

These golden files represent the expected, correct outputs for each model run.

---

### Running Regression Tests

From the project root:

```bash
pytest tests/test_timing_prediction.py
pytest tests/test_length_prediction.py
```

Pytest will automatically:
- run all tests under `drexel_ice/tests/`
- execute each ML pipeline end-to-end
- compare outputs against their golden files
- report any mismatches

If every output matches its golden reference, the system is fully consistent.


## Documentation

For detailed usage instructions and examples, please refer to:

- [usage_examples.md](usage_examples.md): Comprehensive guide with code examples for all tools
- API documentation in the source code comments

## Contributing

Contributions to this project are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

- [ ] [Invite team members and collaborators](https://docs.gitlab.com/ee/user/project/members/)
- [ ] [Create a new merge request](https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html)
- [ ] [Automatically close issues from merge requests](https://docs.gitlab.com/ee/user/project/issues/managing_issues.html#closing-issues-automatically)
- [ ] [Enable merge request approvals](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/)
- [ ] [Set auto-merge](https://docs.gitlab.com/user/project/merge_requests/auto_merge/)

## More Resources

For detailed usage instructions and examples, please see:

- [Usage Examples Documentation](usage_examples.md): Comprehensive guide with detailed code examples, command-line options, and workflows for all tools in this repository.

- [Machine Learning Use Cases](usage_examples.md#machine-learning-use-cases): Detailed explanation of the machine learning models included in this repository and how they leverage the EDA schema ontology.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This project is part of the research on AI/ML techniques for Electronic Design Automation.
- Thanks to all contributors who have helped build and improve this toolset.
