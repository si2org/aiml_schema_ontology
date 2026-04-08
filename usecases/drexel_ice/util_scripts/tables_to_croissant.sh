#!/bin/bash
# Script to process EDA schema samples with DXLCroissant.py
# This script converts multiple EDA schema tables from CSV format to a combined Croissant JSON format

# Function to display usage information
usage() {
    echo "Usage: $0 [OPTION]"
    echo "Convert EDA schema tables from CSV to Croissant JSON format"
    echo
    echo "Options:"
    echo "  -h, --help                 Display this help message"
    echo "  -i, --individual FILE      Create individual Croissant file from specified CSV table"
    echo "  -d, --directory DIR        Process all tables in the specified directory"
    echo "      --tables-only          Only process table.csv files in directory mode"
    echo "      --graph-tables-only    Only process graph_table.csv files in directory mode"
    echo "  -c, --combined FILE        Create combined Croissant file with output to specified file"
    echo
    echo "Examples:"
    echo "  $0 -i ./eda_schema_samples/data/csv_json/wires/table.csv"
    echo "  $0 -d ./eda_schema_samples"
    echo "  $0 -d ./eda_schema_samples --tables-only"
    echo "  $0 -d ./eda_schema_samples --graph-tables-only"
    echo "  $0 -c ./edaschema_metadata_croissant_format_combined.json"
    exit 1
}

# Function to create individual Croissant JSON files from CSV tables
create_individual_croissant_file() {
    local table_path="$1"
    local base_name
    local output_path
    # Support both table.csv and graph_table.csv
    if [[ "$table_path" == *"/table.csv" ]]; then
        base_name=$(basename $(dirname "$table_path"))
        output_path="$(dirname "$table_path")/${base_name}.croissant.json"
    elif [[ "$table_path" == *"/graph_table.csv" ]]; then
        base_name=$(basename $(dirname "$table_path"))
        output_path="$(dirname "$table_path")/${base_name}_graph.croissant.json"
    else
        echo "Unsupported file: $table_path"
        return 1
    fi
    echo "Processing $table_path -> $output_path"
    python ontology/DXLCroissant.py --table "$table_path" --croissant "$output_path"
    return $?
}

# Function to process all table.csv files in a directory
process_all_tables_in_directory() {
    local directory="$1"
    local mode="${2:-both}"
    echo "Searching for tables in $directory (mode: $mode)..."
    local find_expr
    if [ "$mode" = "tables" ]; then
        find_expr="-name table.csv"
    elif [ "$mode" = "graph_tables" ]; then
        find_expr="-name graph_table.csv"
    else
        find_expr="( -name table.csv -o -name graph_table.csv )"
    fi

    for table_path in $(find "$directory" $find_expr); do
        create_individual_croissant_file "$table_path"
    done
    echo "Completed processing all tables."
}

combined_croissant_file() {
    local croissant_file="$1"
    # Process physical design tables
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/wires/table.csv   # Process wires information
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/area_metrics/table.csv   # Process area metrics

    # Process circuit elements tables
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/pins/table.csv   # Process pins information
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/gates/table.csv   # Process gates information
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/timing_graphs/table.csv   # Process timing graphs information
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/timing_graphs/graph_table.csv   # Process timing_graphs graph table
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/netlists/table.csv   # Process netlists information
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/netlists/graph_table.csv   # Process netlists graph table
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/clock_trees/table.csv   # Process clock trees information
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/clock_trees/graph_table.csv   # Process clock_trees graph table

    # Process timing and performance data
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/stages/table.csv   # Process stages information
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/timing_metrics/table.csv   # Process timing metrics information
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/cell_metrics/table.csv   # Process cell metrics information
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/timing_paths/table.csv   # Process timing paths information
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/timing_paths/graph_table.csv   # Process timing_paths graph table

    # Process connectivity and cell data
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/nets/table.csv   # Process nets information
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/nets/graph_table.csv   # Process nets graph table
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/standard_cells/table.csv   # Process standard cells information
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/timing_path_pins/table.csv   # Process timing path pins information
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/ports/table.csv   # Process ports information
    python ontology/DXLCroissant.py --append --croissant "$croissant_file" --table ./eda_schema_samples/data/csv_json/power_metrics/table.csv   # Process power metrics information
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    usage
fi

tables_only=0
graph_tables_only=0

declare -a POSITIONAL_ARGS=()

while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help)
            usage
            ;;
        -i|--individual)
            if [ -z "$2" ]; then
                echo "Error: Individual mode requires a table.csv or graph_table.csv file path"
                usage
            fi
            create_individual_croissant_file "$2"
            shift 2
            ;;
        -d|--directory)
            if [ -z "$2" ]; then
                echo "Error: Directory mode requires a directory path"
                usage
            fi
            dir_arg="$2"
            shift 2
            mode="both"
            while [[ "$1" == --tables-only || "$1" == --graph-tables-only ]]; do
                if [ "$1" == "--tables-only" ]; then
                    mode="tables"
                elif [ "$1" == "--graph-tables-only" ]; then
                    mode="graph_tables"
                fi
                shift
            done
            process_all_tables_in_directory "$dir_arg" "$mode"
            ;;
        -c|--combined)
            if [ -z "$2" ]; then
                echo "Error: Combined mode requires an output file path"
                usage
            fi
            combined_croissant_file "$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done