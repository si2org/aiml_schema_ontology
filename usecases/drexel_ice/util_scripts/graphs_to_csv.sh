#!/bin/bash
# filepath: /Users/amit/work/AIML_Schema_Ontology/graphs_to_csv.sh
# Script to process timing graph JSON files with DXLTables.py from the ontology directory
# This script converts graph JSON files in the format <circuit>-id-<idnumber>-<phase>.json to CSV format
#
# Note: This script assumes it's being run from the root directory of the project
# and that DXLTables.py is in the ontology/ directory

# Function to display usage information
usage() {
    echo "Usage: $0 [OPTION]"
    echo "Convert graph JSON files to CSV format with added metadata columns"
    echo
    echo "Options:"
    echo "  -h, --help                 Display this help message"
    echo "  -d, --directory DIR        Process all graphs in the specified directory (recursively)"
    echo "  -s, --single-graph DIR     Process a specific graph directory"
    echo "  -o, --output DIR           Specify output directory for CSV files (optional)"
    echo "  -a, --all                  Process all graph directories in the EDA schema samples"
    echo
    echo "Examples:"
    echo "  $0 -d ./eda_schema_samples/data/csv_json/timing_graphs/graphs"
    echo "  $0 -s ./eda_schema_samples/data/csv_json/timing_graphs/graphs -o ./output_csv"
    echo "  $0 -a"
    exit 1
}

# Function to process a single graph directory
process_graph_directory() {
    local input_dir="$1"
    local output_dir="$2"
    
    echo "Processing graph files in $input_dir..."
    
    # Build the command using the virtual environment's Python
    local cmd="python ontology/DXLTables.py --input \"$input_dir\""
    if [ -n "$output_dir" ]; then
        cmd="$cmd --output \"$output_dir\""
    fi
    
    # Execute the command
    eval "$cmd"
    
    return $?
}

# Function to process all graph directories in EDA schema samples
process_all_graph_directories() {
    local output_dir="$1"
    local base_dir="./eda_schema_samples/data/csv_json"
    
    echo "Processing all graph directories in $base_dir ..."
    
    # Find all 'graphs' directories
    find "$base_dir" -type d -name "graphs" | while read -r graph_dir; do
        echo "Found graph directory: $graph_dir"
        # Get the graph type (parent directory of 'graphs')
        local graph_type
        graph_type=$(basename "$(dirname "$graph_dir")")
        local custom_output_dir="$output_dir"
        if [ -n "$output_dir" ]; then
            custom_output_dir="$output_dir/$graph_type"
            mkdir -p "$custom_output_dir"
        fi
        process_graph_directory "$graph_dir" "$custom_output_dir"
    done
}

# Check if the script is being run from the root directory
if [ ! -d "ontology" ] || [ ! -f "ontology/DXLTables.py" ]; then
    echo "Error: This script must be run from the root directory of the project"
    echo "Please change to the root directory and try again"
    exit 1
fi

# Parse command line arguments
if [ $# -eq 0 ]; then
    usage
fi

# Initialize variables
INPUT_DIR=""
OUTPUT_DIR=""
PROCESS_ALL=false

# Parse command line arguments
while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help)
            usage
            ;;
        -d|--directory)
            if [ -z "$2" ]; then
                echo "Error: Directory mode requires a directory path"
                usage
            fi
            INPUT_DIR="$2"
            shift 2
            ;;
        -s|--single-graph)
            if [ -z "$2" ]; then
                echo "Error: Single graph mode requires a directory path"
                usage
            fi
            INPUT_DIR="$2"
            shift 2
            ;;
        -o|--output)
            if [ -z "$2" ]; then
                echo "Error: Output option requires a directory path"
                usage
            fi
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -a|--all)
            PROCESS_ALL=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Check if the script should process all graph directories
if [ "$PROCESS_ALL" = true ]; then
    process_all_graph_directories "$OUTPUT_DIR"
    exit 0
fi

# Check if an input directory was specified
if [ -z "$INPUT_DIR" ]; then
    echo "Error: No input directory specified"
    usage
fi

# Check if the input directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' does not exist"
    exit 1
fi

# Process the specified directory
process_graph_directory "$INPUT_DIR" "$OUTPUT_DIR"
