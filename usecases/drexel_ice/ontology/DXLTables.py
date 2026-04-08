#!/usr/bin/env python3
# filepath: /Users/amit/work/AIML_Schema_Ontology/ontology/DXLTables.py
import json
import os
import re
import csv
import glob
import argparse
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd  # Added for DataFrame support

class DXLTables:
    """
    A utility class for converting graph JSON files to CSV format with additional metadata columns.
    This class processes JSON files with the naming pattern <circuit>-id-<idnumber>-<phase>.json
    and converts them to CSVs with additional columns for circuit, id, phase, and the data from the JSON file.
    """
    
    def __init__(self):
        """Initialize a new DXLTables object."""
        self.json_file_pattern = r"(?P<circuit>.+)-id-(?P<idnumber>\d+)-(?P<phase>.+)\.json"
        
    def parse_filename(self, filename: str) -> Optional[Dict[str, str]]:
        """
        Parse a filename to extract circuit, id, and phase information.
        
        Args:
            filename: The filename to parse
            
        Returns:
            A dictionary with circuit, idnumber, and phase information if the pattern matches,
            None otherwise
        """
        print(f"DEBUG: Parsing filename {filename} with pattern {self.json_file_pattern}")
        match = re.match(self.json_file_pattern, os.path.basename(filename))
        if match:
            print(f"DEBUG: Match found: {match.group(0)}")
            print(f"DEBUG: Groups: circuit={match.group('circuit')},\n idnumber={match.group('idnumber')}, \n phase={match.group('phase')}")
            return match.groupdict()
        print(f"DEBUG: No match found for filename {filename}")
        return None
    
    def convert_json_to_csv(self, json_file_path: str, output_dir: str = None) -> str:
        """
        Convert a single JSON graph file to CSV format.
        
        Args:
            json_file_path: Path to the JSON file to convert
            output_dir: Optional directory to save the output CSV file. If None, uses the same directory as the JSON file.
            
        Returns:
            Path to the created CSV file
        """
        # Parse the filename to extract metadata
        filename_info = self.parse_filename(json_file_path)
        if not filename_info:
            raise ValueError(f"Filename {json_file_path} does not match the expected pattern: <circuit>-id-<idnumber>-<phase>.json")
        
        # Read the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Determine the output directory and filename
        if output_dir is None:
            output_dir = os.path.dirname(json_file_path)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Construct the output CSV filename
        output_filename = f"{filename_info['circuit']}-id-{filename_info['idnumber']}.csv"
        output_path = os.path.join(output_dir, output_filename)
        
        # Prepare data for CSV
        graph_type = self._get_graph_type(os.path.dirname(json_file_path))
        rows = self.prepare_csv_rows(data, filename_info, graph_type=graph_type)
        
        # Write to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(rows[0])  # Header
            writer.writerows(rows[1:])  # Data
        
        return output_path
    
    def _get_graph_type(self, input_dir: str) -> str:
        """
        Infer the graph type from the input directory path (e.g., nets, clock_trees, timing_paths).
        """
        # Get the path components
        path_parts = os.path.normpath(input_dir).split(os.sep)
        
        # Look for known graph types in the path
        known_types = ['nets', 'clock_trees', 'timing_paths', 'netlists', 'timing_graphs']
        for graph_type in known_types:
            if graph_type in path_parts:
                print(f"DEBUG: Inferred graph type from path {input_dir}: {graph_type}")
                return graph_type
                
        # Fallback to the parent directory if we can identify 'graphs' as the last component
        if path_parts and path_parts[-1] == 'graphs' and len(path_parts) > 1:
            parent_dir = path_parts[-2]
            print(f"DEBUG: Inferred graph type from parent directory: {parent_dir}")
            return parent_dir
            
        # Last resort: use the last directory name
        last_dir = os.path.basename(os.path.normpath(input_dir))
        print(f"DEBUG: Fallback graph type from path {input_dir}: {last_dir}")
        return last_dir

    def prepare_csv_rows(self, data: Dict[str, Any], filename_info: Dict[str, str], graph_type: str = "") -> List[List[str]]:
        """
        Prepare rows for CSV output, with special handling for nets, clock_trees, and timing_paths.
        
        Args:
            data: The graph data from the JSON file
            filename_info: Dictionary with circuit, idnumber, and phase information
            graph_type: Optional graph type (nets, clock_trees, timing_paths) to adjust CSV structure
            
        Returns:
            List of rows to write to the CSV file, including header
        """
        rows = []
        phase = filename_info['phase']
        circuit = filename_info['circuit']
        id_num = filename_info['idnumber']
        # Special handling for graph types
        print(f"Preparing CSV rows for graph type: {graph_type} --- circuit: {circuit}, id: {id_num}, phase: {phase}")
        if graph_type == 'nets':
            header = ['circuit', 'id', 'phase', 'net_source', 'target', 'source_type', 'target_type']
            rows.append(header)
        elif graph_type == 'clock_trees':
            header = ['circuit', 'id', 'phase', 'clock_source', 'source', 'target', 'source_type', 'target_type']
            rows.append(header)
        elif graph_type == 'timing_paths':
            header = ['circuit', 'id', 'phase', 'startpoint', 'endpoint', 'path_type', 'sort_index', 'source', 'target', 'source_type', 'target_type']
            rows.append(header)
        else:
            header = ['circuit', 'id', 'phase', 'source', 'target', 'source_type', 'target_type']
            rows.append(header)
        
        # Extract circuit, id, and phase from filename_info
        # Process edges to create data rows
        if 'edges' in data and 'nodes' in data and 'node_types' in data:
            nodes = data['nodes']
            node_types = data['node_types']
            edges = data['edges']
            
            # Map nodes to their types
            node_type_map = {node: node_type for node, node_type in zip(nodes, node_types)}
            
            # Process each edge
            for edge in edges:
                if len(edge) >= 2:
                    source = edge[0]
                    target = edge[1]
                    source_type = node_type_map.get(source, "UNKNOWN")
                    target_type = node_type_map.get(target, "UNKNOWN")
                    # Special row handling
                    if graph_type == 'nets':
                        # source: detailed_route-net90 -> phase, net_source
                        if '-' in source:
                            phase_val, net_source = source.split('-', 1)
                        else:
                            phase_val, net_source = phase, source
                        row = [circuit, id_num, phase_val, net_source, target, source_type, target_type]
                    elif graph_type == 'clock_trees':
                        # phase: detailed_place-clk -> phase, clock_source
                        if '-' in phase:
                            phase_val, clock_source = phase.split('-', 1)
                        else:
                            phase_val, clock_source = phase, ""
                        row = [circuit, id_num, phase_val, clock_source, source, target, source_type, target_type]
                    elif graph_type == 'timing_paths':
                        # phase: detailed_route-382-411-max-2 -> phase, startpoint, endpoint, path_type, sort_index
                        parts = phase.split('-')
                        if len(parts) == 5:
                            phase_val, startpoint, endpoint, path_type, sort_index = parts
                        else:
                            phase_val, startpoint, endpoint, path_type, sort_index = phase, "", "", "", "0"
                        row = [circuit, id_num, phase_val, startpoint, endpoint, path_type, sort_index, source, target, source_type, target_type]
                    else:
                        row = [circuit, id_num, phase, source, target, source_type, target_type]
                    rows.append(row)
        
        return rows
    
    def process_directory(self, input_dir: str, output_dir: Optional[str] = None) -> List[str]:
        """
        Process all JSON files in a directory.
        
        Args:
            input_dir: Directory containing JSON files to process
            output_dir: Optional directory to save output CSV files. If None, uses the same directory as each JSON file.
            
        Returns:
            List of paths to created CSV files
        """
        # Find all JSON files in the directory
        json_files = []
        for root, _, files in os.walk(input_dir):
            for file in files:
                if file.endswith('.json') and re.match(self.json_file_pattern, file):
                    json_files.append(os.path.join(root, file))
        
        if not json_files:
            print(f"No matching JSON files found in {input_dir}")
            return []
        
        # Group JSON files by circuit and ID
        grouped_files = {}
        for json_file in json_files:
            filename_info = self.parse_filename(json_file)
            if filename_info:
                key = (filename_info['circuit'], filename_info['idnumber'])
                if key not in grouped_files:
                    grouped_files[key] = []
                grouped_files[key].append((json_file, filename_info))
        
        # Process each group of JSON files
        processed_files = []
        for (circuit, id_num), file_infos in grouped_files.items():
            try:
                # Determine output directory
                if output_dir is None:
                    output_dir = os.path.dirname(file_infos[0][0])
                
                # Create output directory if it doesn't exist
                os.makedirs(output_dir, exist_ok=True)
                
                # Construct the output CSV filename
                output_filename = "graph_table.csv"
                output_path = os.path.join(output_dir, output_filename)
                
                # Use new header/row logic
                with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    for idx, (json_file, filename_info) in enumerate(file_infos):
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        #graph_type = self._get_graph_type(json_file)
                        graph_type = self._get_graph_type(os.path.dirname(json_file))
                        rows = self.prepare_csv_rows(data, filename_info, graph_type=graph_type)
                        # Write header only for first file
                        if idx == 0:
                            writer.writerow(rows[0])
                        # Write data for all files
                        writer.writerows(rows[1:])
                
                processed_files.append(output_path)
                # Post-process for phase splitting if needed
                # self.preprocess_graph_table_csv(output_path)
                print(f"Converted {len(file_infos)} JSON files to {output_path}")
            except Exception as e:
                print(f"Error processing files for {circuit}-id-{id_num}: {e}")
        return processed_files

    @staticmethod
    def load_all_csvs_as_dataframe(directory: str) -> 'pd.DataFrame':
        """
        Load all CSV files generated by DXLTables from a directory into a single pandas DataFrame.
        
        Args:
            directory: Directory containing the CSV files (e.g., output from DXLTables)
            
        Returns:
            pandas DataFrame containing concatenated data from all CSVs
        """
        csv_files = glob.glob(os.path.join(directory, "*-id-*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV files matching '*-id-*.csv' found in {directory}")
        df_list = [pd.read_csv(f) for f in csv_files]
        return pd.concat(df_list, ignore_index=True)
    @staticmethod
    def load_all_graph_tables_as_dataframe(directory: str, recursive: bool = True, filename_pattern: str = "graph_table.csv") -> 'pd.DataFrame':
        """
        Load all 'graph_table.csv' files from a directory (recursively by default) into a single pandas DataFrame.
        
        Args:
            directory: Root directory to search for 'graph_table.csv' files.
            recursive: If True, search subdirectories recursively.
            filename_pattern: Pattern of filenames to search for (default: "graph_table.csv").
            
        Returns:
            pandas DataFrame containing concatenated data from all found CSVs
        """
        pattern = f'**/{filename_pattern}' if recursive else filename_pattern
        csv_files = glob.glob(os.path.join(directory, pattern), recursive=recursive)
        if not csv_files:
            raise FileNotFoundError(f"No '{filename_pattern}' files found in {directory}")
        df_list = [pd.read_csv(f) for f in csv_files]
        return pd.concat(df_list, ignore_index=True)
   

def main():
    """Main function to parse arguments and process files."""
    parser = argparse.ArgumentParser(
        prog="DXLTables",
        description="Convert graph JSON files to CSV format with additional metadata columns",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('--input', required=True, 
                        help='Input directory containing JSON files')
    parser.add_argument('--output', 
                        help='Output directory for CSV files. If not specified, uses the same directory as the input JSON files.')
    
    args = parser.parse_args()
    
    dxl_tables = DXLTables()
    
    if os.path.isdir(args.input):
        processed_files = dxl_tables.process_directory(args.input, args.output)
        if processed_files:
            print(f"Created {len(processed_files)} CSV files")
        else:
            print("No CSV files were created")
    else:
        print(f"Input {args.input} is not a valid directory")
        return 1
    
    return 0

if __name__ == "__main__":
    main()
    # Example: Load all generated CSVs as a pandas DataFrame (uncomment to use)
    # df = DXLTables.load_all_csvs_as_dataframe("./processed_graphs/timing_graphs")
    # print(df.head())
