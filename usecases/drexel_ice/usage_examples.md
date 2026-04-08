# EDA Schema Processing Tools - User Guide

This document provides comprehensive instructions for using the suite of tools designed for processing Electronic Design Automation (EDA) schema data. While the README.md file provides a high-level overview of the project, this guide offers detailed examples, workflows, and technical details for working with the tools in this repository.


## Data Analysis with Pandas

```python
import pandas as pd
from ontology.DXLTables import DXLTables

# Load CSV files with *-id-*.csv pattern (older format)
df = DXLTables.load_all_csvs_as_dataframe("./path/to/csv/directory")
print(df.head())
```

### Load Consolidated Graph Tables

```python
import pandas as pd
from ontology.DXLTables import DXLTables

# Load all graph_table.csv files recursively (newer consolidated format)
df = DXLTables.load_all_graph_tables_as_dataframe("./path/to/csv/directory")
```

## Table of Contents

- [Data Analysis with Pandas](#data-analysis-with-pandas)
- [Overview of Tools](#overview-of-tools)
- [Python Requirements](#python-requirements)
- [DXLCroissant - CSV to Croissant JSON Converter](#dxlcroissant---csv-to-croissant-json-converter)
- [DXLTables - Graph JSON to CSV Converter](#dxltables---graph-json-to-csv-converter)
- [tables_to_croissant.sh - Shell Wrapper for DXLCroissant](#tables_to_croissantsh---shell-wrapper-for-dxlcroissant)
- [graphs_to_csv.sh - Shell Wrapper for DXLTables](#graphs_to_csvsh---shell-wrapper-for-dxltables)
- [EDA Schema Ontology - Core Utilities](#eda-schema-ontology---core-utilities)
- [Machine Learning Use Cases](#machine-learning-use-cases)
  - [Net Length Prediction](#net-length-prediction-length_predictionpy)
  - [Timing Path Prediction](#timing-path-prediction-timing_predictionpy)
- [Common Workflows](#common-workflows)
- [Development Environment](#development-environment)

## Overview of Tools

The EDA Schema Processing Tools suite consists of four main components:

1. **ontology/DXLCroissant.py**: Python utility for converting EDA schema table files (CSV) to Croissant metadata format (JSON)
2. **ontology/DXLTables.py**: Python utility for converting graph representation JSON files to CSV format with metadata columns
3. **tables_to_croissant.sh**: Shell wrapper to streamline processing of CSV tables with DXLCroissant.py
4. **graphs_to_csv.sh**: Shell wrapper to simplify processing of graph JSON files with DXLTables.py

Together, these tools provide a complete workflow for converting EDA schema data between different formats, making it easier to analyze and integrate this data into machine learning pipelines.

The repository also includes:

1. **ontology/eda_schema_ontology.py**: Core utilities for working with the EDA ontology and building graphs
2. **usecases/**: Example applications using the ontology and tools
   - **length_prediction.py**: Neural network for predicting net lengths
   - **timing_prediction.py**: Graph neural network for predicting timing characteristics

## Python Requirements

Before using the tools, you need to install the required Python dependencies. A `requirements.txt` file is provided in the repository for easy installation.

### Required Packages

The following Python packages are required:

- **pandas**: For data manipulation and analysis
- **mlcroissant**: For working with Croissant metadata format
- **rdflib**: For RDF graph handling and ontology processing
- **graphviz**: For graph visualization
- **pytest**: For running the test suite
- **grpcio**: For gRPC functionality
- **grpcio-tools**: For gRPC code generation
- **protobuf**: For Protocol Buffers support

### Installation

To install all required dependencies, run:

```bash
pip install -r requirements.txt
```

If you're using a virtual environment (recommended), activate it first:

```bash
# Create a virtual environment (if not already created)
python -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Note**: If you encounter any issues with the `grpcio-tools` installation, make sure you're using the correct package name. Do not use `grpc-tools` as it's not the official package.

## DXLCroissant - CSV to Croissant JSON Converter

DXLCroissant is a Python utility for converting EDA schema table files (CSV) to Croissant metadata format (JSON).

### Basic Usage

#### Process a Single Table File

To convert a single CSV table to Croissant format:

```bash
python ontology/DXLCroissant.py --table /path/to/table.csv --croissant output.json
```

This will create a new Croissant metadata file named `output.json` containing metadata for the specified table.

#### Process Multiple Table Files

To process multiple table.csv files and combine their metadata:

```bash
python ontology/DXLCroissant.py --tables /path/to/dir1/table.csv /path/to/dir2/table.csv --croissant output.json
```

This will remove any existing `output.json` file and generate a new Croissant metadata file containing combined metadata for all specified tables.

If you want to append to an existing file rather than replace it, add the `--append` flag:

```bash
python ontology/DXLCroissant.py --tables /path/to/dir1/table.csv /path/to/dir2/table.csv --append --croissant output.json
```

#### Process All Table Files in a Directory

To find and process all table.csv files in a directory:

```bash
python ontology/DXLCroissant.py --dir /path/to/directory --croissant output.json
```

This will search for all files named `table.csv` in the specified directory (including subdirectories), process them, and generate a Croissant metadata file named `output.json` containing combined metadata for all found tables.

### Advanced Usage

#### Specify Publication Date

You can specify a custom publication date for the metadata:

```bash
python ontology/DXLCroissant.py --table /path/to/table.csv --croissant output.json --date 2023-12-31
```

If not specified, the current date will be used.

#### Append to Existing File

You can append to an existing Croissant metadata file instead of overwriting it:

```bash
# First, create a metadata file for one table
python ontology/DXLCroissant.py --table /path/to/dir1/table.csv --croissant output.json

# Then, append metadata for another table
python ontology/DXLCroissant.py --table /path/to/dir2/table.csv --croissant output.json --append
```

This is useful for incrementally building a combined metadata file.

### Notes

- The tool expects input CSV files to follow a specific naming pattern. Files should be named `table.csv` and located in directories that match the logical name of the dataset.
- When using `--tables` or `--dir`, the output metadata will include combined information from all processed tables.
- When appending with `--append`, the tool will preserve existing metadata and add the new distribution and recordSet entries.

## DXLTables - Graph JSON to CSV Converter

DXLTables is a Python utility for converting graph JSON files to CSV format with additional metadata columns. It processes JSON files with a specific naming pattern and extracts relevant information for analysis.

### Basic Usage

#### Process a Single Directory of Graph Files

To convert all graph JSON files in a directory to CSV format:

```bash
python ontology/DXLTables.py --input /path/to/graph/directory
```

This will process all JSON files in the specified directory that match the pattern `<circuit>-id-<idnumber>-<phase>.json`, extract the graph data, and generate a consolidated CSV file named `graph_table.csv` containing data from all phases.

#### Specify Output Directory

You can specify a custom output directory for the generated CSV files:

```bash
python ontology/DXLTables.py --input /path/to/graph/directory --output /path/to/output/directory
```

If not specified, the CSV files will be created in the same directory as the input JSON files.

### How It Works

DXLTables processes JSON files following these steps:

1. **Filename Parsing**: Files with the pattern `<circuit>-id-<idnumber>-<phase>.json` are identified and parsed to extract circuit name, ID number, and phase information.

2. **File Grouping**: JSON files are grouped by circuit and ID. For example, all files with the same circuit name and ID but different phases will be processed together into a single output file.

3. **Data Extraction**: For each JSON file, the tool extracts:
   - Nodes (identifiers)
   - Node types (classifications)
   - Edges (connections between nodes)

4. **CSV Generation**: The tool creates a consolidated `graph_table.csv` file with these columns:
   - `circuit`: The circuit name extracted from the filename
   - `id`: The ID number extracted from the filename
   - `phase`: The phase information extracted from the filename
   - `source`: The source node of an edge
   - `target`: The target node of an edge
   - `source_type`: The type of the source node
   - `target_type`: The type of the target node
   
   Different graph types may include additional columns for specific data:
   - Nets graphs: `net_source` column
   - Clock tree graphs: `clock_source` column
   - Timing path graphs: `startpoint`, `endpoint`, `path_type`, and `sort_index` columns

### Input JSON Format

The input JSON files must have the following structure:

```json
{
  "nodes": ["node1", "node2", "node3", ...],
  "node_types": ["TYPE_A", "TYPE_B", "TYPE_A", ...],
  "edges": [
    ["node1", "node2"],
    ["node2", "node3"],
    ...
  ]
}
```

### Notes

- The tool requires input JSON files to have a specific structure with `nodes`, `node_types`, and `edges` fields.
  - `nodes`: Array of node identifiers
  - `node_types`: Array of types corresponding to each node in the `nodes` array
  - `edges`: Array of edge definitions, where each edge is an array with at least two elements [source, target]
- The generated CSV files combine data from multiple phases of the same circuit ID into a single file.
- This allows for easier analysis of how graph structures evolve across different phases.
- The tool automatically groups JSON files by circuit and ID, so you don't need to manually specify which files belong together.
- For best results, ensure all JSON files follow the naming convention exactly.

### Data Analysis with Pandas

DXLTables provides utility methods to load the generated CSV files into pandas DataFrames for further analysis:

#### Load Individual CSV Files

```python
import pandas as pd
from ontology.DXLTables import DXLTables

# Load CSV files with *-id-*.csv pattern (older format)
df = DXLTables.load_all_csvs_as_dataframe("./path/to/csv/directory")
print(df.head())
```

#### Load Consolidated Graph Tables

```python
import pandas as pd
from ontology.DXLTables import DXLTables

# Load all graph_table.csv files recursively (newer consolidated format)
df = DXLTables.load_all_graph_tables_as_dataframe("./path/to/csv/directory")

# With custom options
df = DXLTables.load_all_graph_tables_as_dataframe(
    "./path/to/csv/directory", 
    recursive=True,
    filename_pattern="graph_table.csv"
)

# Analyze the data
print(f"Total edges: {len(df)}")
print(f"Unique circuits: {df['circuit'].nunique()}")
print(f"Unique phases: {df['phase'].unique()}")
```

These utility methods make it easy to load and analyze graph data from multiple CSV files in a single pandas DataFrame.

## tables_to_croissant.sh - Shell Wrapper for DXLCroissant

`tables_to_croissant.sh` is a shell script that provides a user-friendly interface for the DXLCroissant.py utility, making it easier to process EDA schema tables and convert them to Croissant JSON format.

### Basic Usage

#### Display Help Information

To view usage information and available options:

```bash
./util_scripts/tables_to_croissant.sh -h
```

#### Process an Individual Table File

To create a Croissant JSON file from a specific CSV table:

```bash
./util_scripts/tables_to_croissant.sh -i ./eda_schema_samples/data/csv_json/wires/table.csv
```

This will process the specified table.csv file and generate a corresponding Croissant JSON file in the same directory.

#### Process All Tables in a Directory

To process all table.csv files found in a directory and its subdirectories:

```bash
./util_scripts/tables_to_croissant.sh -d ./eda_schema_samples
```

This will search for all files named `table.csv` in the specified directory, process each one, and generate individual Croissant JSON files.

You can specify which file types to process:

```bash
# Process only regular table.csv files (exclude graph tables)
./util_scripts/tables_to_croissant.sh -d ./eda_schema_samples --tables-only

# Process only graph_table.csv files
./util_scripts/tables_to_croissant.sh -d ./eda_schema_samples --graph-tables-only
```

#### Create a Combined Croissant File

To create a single combined Croissant JSON file from all tables:

```bash
./util_scripts/tables_to_croissant.sh -c ./edaschema_metadata_croissant_format_combined.json
```

This will find and process all table.csv files in the default directory (`./eda_schema_samples`) and generate a single combined Croissant JSON file at the specified path.

### Notes

- The script assumes a specific directory structure with table.csv files located in component-specific directories.
- It automatically extracts component names from the directory structure for proper metadata generation.
- When creating individual files, the output is saved to the same directory as the input CSV file.
- When creating a combined file, all tables are processed and their metadata is combined into a single JSON file.

## graphs_to_csv.sh - Shell Wrapper for DXLTables

`graphs_to_csv.sh` is a shell script that provides a user-friendly interface for the DXLTables.py utility, making it easier to process graph JSON files and convert them to CSV format with metadata columns.

### Basic Usage

#### Display Help Information

To view usage information and available options:

```bash
./util_scripts/graphs_to_csv.sh -h
```

#### Process a Specific Graph Directory

To process all graph JSON files in a specific directory:

```bash
./util_scripts/graphs_to_csv.sh -d ./eda_schema_samples/data/csv_json/timing_graphs/graphs
```

This will process all JSON files in the specified directory that match the pattern `<circuit>-id-<idnumber>-<phase>.json` and generate a consolidated `graph_table.csv` file containing data from all phases.

#### Process a Single Graph with Custom Output Directory

To process a specific graph directory and save the output CSV files to a custom location:

```bash
./util_scripts/graphs_to_csv.sh -s ./eda_schema_samples/data/csv_json/timing_graphs/graphs -o ./output_csv
```

This will process all JSON files in the specified directory and save the generated `graph_table.csv` file to the specified output directory.

#### Process All Graph Directories

To process all graph directories found in the EDA schema samples:

```bash
./util_scripts/graphs_to_csv.sh -a
```

This will search for all directories named `graphs` within `./eda_schema_samples/data/csv_json/`, process each one, and generate a `graph_table.csv` file for each graph directory.

You can also specify a custom output directory when processing all graphs:

```bash
./util_scripts/graphs_to_csv.sh -a -o ./all_graphs_output
```

### Command-Line Options

- `-h, --help`: Display help message
- `-d, --directory DIR`: Process all graphs in the specified directory (recursively)
- `-s, --single-graph DIR`: Process a specific graph directory
- `-o, --output DIR`: Specify output directory for CSV files (optional)
- `-a, --all`: Process all graph directories in the EDA schema samples

### Notes

- The script automatically handles the recursive search for JSON files that match the expected pattern.
- It groups files by circuit and ID, combining data from multiple phases into a single `graph_table.csv` file.
- The generated CSV file includes metadata columns that make it easier to analyze the graph data.
- The `-a` option is particularly useful for batch processing all graph directories in a standard EDA schema project.
- Example of the output CSV structure:

```
circuit,id,phase,source,target,source_type,target_type
gcd,000001,place,cell_1,cell_2,CELL,CELL
gcd,000001,place,cell_2,net_5,CELL,NET
gcd,000001,route,cell_1,cell_2,CELL,CELL
```

## Machine Learning Use Cases

This repository includes example machine learning models that leverage the EDA schema ontology for prediction tasks. These examples demonstrate how to use the ontology for real-world machine learning applications in EDA.

### Net Length Prediction (`usecases/length_prediction`)

The `length_prediction` module implements a feedforward neural network model that predicts net wire lengths after routing based on pre-routing features.

#### Model Architecture

```
Input (2 features) → Hidden Layer (32 units) → Hidden Layer (16 units) → Output (1 unit)
```

- **Input Features**: `estimatedHpwl` (half-perimeter wire length) and `numFanout` (number of fanout connections) from the placement phase
- **Target**: `netLength` (actual wire length) from the routing phase
- **Model Type**: Simple 2-layer feedforward neural network with ReLU activations
- **Loss Function**: Mean Squared Error (MSE)

#### Usage Example

```python
import torch
from ontology.eda_schema_ontology import EDA, get_ontology_df
from length_prediction import NetLengthPredictor, load_placement_routing_data, prepare_dataloaders, train, evaluate

# Load data from ontology
X, y = load_placement_routing_data()
train_loader, X_test, y_test = prepare_dataloaders(X, y, batch_size=32)

# Create and train the model
model = NetLengthPredictor()
train(model, train_loader, epochs=500, lr=0.001)

# Evaluate the model
evaluate(model, X_test, y_test)

# Use the model for prediction
model.eval()
with torch.no_grad():
    new_data = torch.tensor([[estimated_hpwl, num_fanout]], dtype=torch.float32)
    predicted_length = model(new_data).item()
    print(f"Predicted net length: {predicted_length:.2f} units")
```

#### How It Works

1. **Data Loading**: Uses `get_ontology_df` to extract features from EDA schema ontology
   ```python
   place_df = get_ontology_df(entity=EDA.Net, phase="detailed_place", 
                             properties=["name", "estimatedHpwl", "numFanout"])
   route_df = get_ontology_df(entity=EDA.Net, phase="detailed_route", 
                             properties=["name", "netLength"])
   ```

2. **Data Preparation**: Merges placement and routing data, standardizes features, and splits into train/test sets

3. **Model Training**: Uses PyTorch's Adam optimizer with MSE loss function to train the neural network

4. **Evaluation**: Reports Mean Absolute Error (MAE) and Maximum Error metrics

#### Benefits

- Allows predicting final wire lengths early in the design flow
- Can help identify potential routing congestion issues
- Simple model architecture demonstrates the value of the ontology data structure

### Timing Path Prediction (`usecases/timing_prediction`)

The `timing_prediction` module implements Graph Neural Network (GNN) models that predict timing characteristics of paths after routing, using only placement-stage data.

#### Model Architecture

Two GNN models are implemented:

1. **DeepGNN**: Basic 2-layer Graph Convolutional Network (GCN)
   ```
   Node Features → GCNConv → ReLU → GCNConv → ReLU → Global Mean Pool → Linear → Output
   ```

2. **WideAndDeepGNN**: Fusion of node-level GNN features with graph-level metadata
   ```
   Node Features → GCNConv → ReLU → GCNConv → ReLU → Global Mean Pool
                                                               ↓
                                                          Concatenate ← Linear(Graph Features) ← Graph Features
                                                               ↓
                                                            Linear → Output
   ```

#### Usage Example

```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from timing_prediction import run

# Predict arrival time using placement data to estimate routing values
run("arrival_time")

# Predict required time using placement data to estimate routing values
run("required_time")

# Predict slack using placement data to estimate routing values 
run("slack")
```

#### How It Works

1. **Graph Loading**: Uses `get_timing_path_graphs` to load timing path graphs from different design phases
   ```python
   placement_graphs = get_timing_path_graphs("detailed_place")
   routing_graphs = get_timing_path_graphs("detailed_route")
   ```

2. **Graph Matching**: Matches source (placement) and target (routing) graphs using composite keys
   ```python
   key = (g.graph.get("netlist_id"), g.graph.get("startpoint"), g.graph.get("endpoint"))
   ```

3. **Feature Extraction**:
   - Node-level numeric features from graph nodes
   - Graph-level features from graph metadata
   - Labels from target graphs (routing phase)

4. **Model Training**: Trains both GNN architectures and evaluates performance:
   - Mean Absolute Error (MAE)
   - Mean Absolute Percentage Error (MAPE)

5. **Prediction**: Can predict various timing metrics (arrival_time, required_time, slack)

#### Benefits

- Early prediction of post-routing timing characteristics
- Graph-based approach captures the structural relationships between pins
- Wide+Deep architecture leverages both local and global features
- Supports multiple timing metrics prediction

## Common Workflows

This section provides examples of common workflows using the EDA Schema Processing Tools.

### Complete Graph Processing Workflow

To process all graph JSON files and convert them to CSV format:

```bash
# Process all graph directories in the EDA schema samples
./util_scripts/graphs_to_csv.sh -a -o ./eda_schema_samples/data/csv_json
```

### Complete Table Processing Workflow

To process all table CSV files and convert them to Croissant JSON format:

```bash
# Process all table.csv files and create a combined Croissant JSON file
./util_scripts/tables_to_croissant.sh -c ./combined_croissant_metadata.json
```

### Combined Graph and Table Workflow

To process both graphs and tables in a complete workflow:

```bash
# Step 1: Process all graph JSON files to CSV format
./util_scripts/graphs_to_csv.sh -a -o ./eda_schema_samples/data/csv_json

# Step 2: Process all table CSV files to Croissant JSON format
./util_scripts/tables_to_croissant.sh -c ./combined_croissant_metadata.json
```

This complete workflow converts all graph JSON files to CSV format with metadata columns and then processes all table CSV files to create a combined Croissant JSON metadata file.

## Development Environment

This project was developed and tested in the following environment:

### Python Environment

- **Python Version**: 3.10.16
- **Environment Management**: pyenv 2.5.3 with virtual environment (.venv)
- **Package Manager**: pip 25.1.1

### Dependencies

The core dependencies used for development include:

```
Package             Version
------------------- -----------------
pandas              2.3.0
mlcroissant         1.0.17
rdflib              7.1.4
graphviz            0.21
pytest              8.4.0
grpcio              1.73.0
grpcio-tools        1.73.0
protobuf            6.31.1
```

A complete list of all dependencies and their versions:

```
Package             Version
------------------- -----------------
absl-py             2.3.0
certifi             2025.6.15
charset-normalizer  3.4.2
decorator           5.2.1
etils               1.12.2
exceptiongroup      1.3.0
fsspec              2025.5.1
graphviz            0.21
grpcio              1.73.0
grpcio-tools        1.73.0
idna                3.10
importlib_resources 6.5.2
iniconfig           2.1.0
isodate             0.7.2
jsonpath-rw         1.4.0
mlcroissant         1.0.17
networkx            3.4.2
numpy               2.2.6
packaging           25.0
pandas              2.3.0
pandas-stubs        2.2.3.250527
pip                 25.1.1
pluggy              1.6.0
ply                 3.11
protobuf            6.31.1
Pygments            2.19.1
pyparsing           3.2.3
pytest              8.4.0
python-dateutil     2.9.0.post0
pytz                2025.2
rdflib              7.1.4
requests            2.32.4
scipy               1.15.3
setuptools          65.5.0
six                 1.17.0
tomli               2.2.1
tqdm                4.67.1
types-pytz          2025.2.0.20250516
typing_extensions   4.14.0
tzdata              2025.2
urllib3             2.4.0
zipp                3.23.0
```

### Operating System

- **OS**: macOS
- **Shell**: zsh

To reproduce this environment, we recommend using a virtual environment:

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

This will ensure that you have the same Python environment and dependencies as used during development.
