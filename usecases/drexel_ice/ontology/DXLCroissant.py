import csv
import json
import os
import hashlib
import argparse
import glob
import tempfile
from datetime import date
from typing import List, Dict, Any, Optional

# DXLCroissant.py - A class for handling Croissant metadata for EDA schemas

class DXLCroissant:
    """
    A class for handling Croissant metadata for EDA schemas.
    Provides functionality to read EDA schema tables and convert them to Croissant format.
    """
    
    def __init__(self, date_published=None):
        """
        Initialize a new DXLCroissant object with empty metadata.
        
        Args:
            date_published: Optional publication date in YYYY-MM-DD format. Defaults to today's date.
        """
        self.metadata = dict(self.METADATA_TEMPLATE)
        self.temp_files = []
        self.date_published = date_published or date.today().isoformat()
    
    # Define metadata template for reuse
    METADATA_TEMPLATE = {
        "@context": {
            "@vocab": "https://schema.org/",
            "sc": "https://schema.org/",
            "cr": "http://mlcommons.org/croissant/",
            "dct": "http://purl.org/dc/terms/",
            "conformsTo": "dct:conformsTo",
            "recordSet": "cr:recordSet",
            "field": "cr:field",
            "dataType": {"@id": "cr:dataType", "@type": "@vocab"},
            "source": "cr:source",
            "extract": "cr:extract",
            "fileObject": "cr:fileObject",
            "column": "cr:column"
        },
        "@type": "sc:Dataset",
        "name": "",  # Will be set for each dataset
        "description": "",  # Will be set for each dataset
        "datePublished": "",  # Will be set based on the provided date
        "version": "1.0.0",
        "license": "MIT",
        "citation": "",  # Will be set for each dataset
        "conformsTo": "http://mlcommons.org/croissant/1.0",
        "url": "",  # Will be set for each dataset
        "distribution": [],
        "recordSet": []
    }

    # Define combined metadata template for reuse
    COMBINED_METADATA_TEMPLATE = {
        **METADATA_TEMPLATE,
        "name": "combined_dataset",
        "description": "Combined dataset from multiple CSV files",
        # datePublished will be set at runtime
        "citation": "Combined Dataset",
        "url": "https://example.com/combined_dataset"
    }
    
    def get_logical_name(self, file_path: str) -> str:
        """
        Map a file path to a logical name for use in metadata.
        This allows customizing how physical file paths are referenced in the schema.
        
        Args:
            file_path: The physical path to the file
            
        Returns:
            A logical name to use in the schema
        """
        path_parts = file_path.split(os.path.sep)
        if path_parts[-1] not in ("table.csv", "graph_table.csv"):
            raise ValueError(f"Path {file_path} does not end with 'table.csv' or 'graph_table.csv'. Expected format: '<something>/<logicalname>/table.csv' or '<logicalname>/table.csv' or 'graph_table.csv'")
        if len(path_parts) < 2:
            raise ValueError(f"Path {file_path} does not contain a directory component. Expected format: '<something>/<logicalname>/table.csv' or '<logicalname>/table.csv'")
        logical_name = path_parts[-2]
        if path_parts[-1] == "table.csv":
            return f"{logical_name}.csv"
        elif path_parts[-1] == "graph_table.csv":
            return f"{logical_name}_graph.csv"
        raise ValueError(f"Unrecognized file ending for {file_path}. Supported: table.csv, graph_table.csv")
    
    def calculate_file_hash(self, file_path: str, hash_algorithm) -> str:
        """
        Calculate hash for a file using the specified algorithm.
        
        Args:
            file_path: Path to the file to hash
            hash_algorithm: Hash algorithm to use (from hashlib)
            
        Returns:
            Hexadecimal string representation of the hash
        """
        hash_obj = hash_algorithm()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    
    def preprocess_graph_table_csv(self, csv_file: str) -> None:  # Marked for deletion
        """
        Preprocess graph_table.csv files to split the 'phase' column into multiple columns as required.
        Modifies the CSV in-place if it matches clock, net, or timing_path entity rules.
        """
        lower_path = csv_file.lower()
        if not lower_path.endswith('graph_table.csv'):
            return  # Not a graph_table.csv, skip
        # Set up split_columns and splitter based on entity type
        if '/clock/' in lower_path:
            split_columns = ['phase', 'clock_source']
            splitter = lambda val: (val.split('-')[0], val.split('-')[1] if '-' in val else '')
        elif '/net/' in lower_path:
            split_columns = ['phase', 'net']
            splitter = lambda val: (val.split('-')[0], val.split('-')[1] if '-' in val else '')
        elif '/timing_path/' in lower_path:
            split_columns = ['phase', 'startpoint', 'endpoint', 'path_type', 'sort_index']
            def splitter(val):
                parts = val.split('-')
                if len(parts) >= 5:
                    return (parts[0], parts[1], parts[2], parts[3], parts[4])
                else:
                    return (val, '', '', '', '')
        else:
            return  # Not a supported entity type, skip

        with open(csv_file, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            data = list(reader)

        new_fieldnames = [fn for fn in fieldnames if fn != 'phase'] + split_columns
        new_rows = []
        for row in data:
            new_row = {k: v for k, v in row.items() if k != 'phase'}
            if 'phase' in row:
                phase_values = splitter(row['phase'])
                for i, col in enumerate(split_columns):
                    new_row[col] = phase_values[i] if i < len(phase_values) else ''
            new_rows.append(new_row)

        with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=new_fieldnames)
            writer.writeheader()
            writer.writerows(new_rows)

    def read_edaschema_table(self, csv_file: str, temp_json_file: Optional[str] = None) -> Dict:
        """
        Read an EDA schema table CSV file and convert it to Croissant metadata.
        
        Args:
            csv_file: Path to the input CSV file
            temp_json_file: Optional path to save the individual JSON metadata
            
        Returns:
            The metadata dictionary for this table
        """
        # Preprocess graph_table.csv if needed
        # self.preprocess_graph_table_csv(csv_file)
        
        with open(csv_file, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header_fieldnames = next(reader)
            data = list(reader)
        
        # Check if the CSV file has data
        if not data:
            raise ValueError(f"CSV file {csv_file} is empty")
        
        # Get the logical name for the CSV file
        csv_logical_name = self.get_logical_name(csv_file)
        csv_id = os.path.splitext(csv_logical_name)[0]
        
        # Extract field names and create a unique record set ID
        # Use the stored fieldnames, which we know are safe
        fieldnames = header_fieldnames
        record_set_id = f"{csv_id}_records"
        
        # Calculate MD5 and SHA256 hashes
        md5_hash = self.calculate_file_hash(csv_file, hashlib.md5)
        sha256_hash = self.calculate_file_hash(csv_file, hashlib.sha256)
        
        # Create metadata using the template
        metadata = dict(self.METADATA_TEMPLATE)
        
        # Add specific metadata for this CSV file
        metadata["name"] = f"{csv_id}_dataset"
        metadata["description"] = f"Dataset containing {csv_id} metrics across different phases"
        metadata["datePublished"] = self.date_published
        metadata["citation"] = f"{csv_id.capitalize()} Dataset"
        metadata["url"] = f"https://example.com/{csv_id}_dataset"
        
        # Add distribution and recordSet entries
        metadata["distribution"] = [
            {
                "@type": "cr:FileObject",
                "@id": csv_logical_name,
                "name": csv_logical_name,
                "contentUrl": csv_file,
                "encodingFormat": "text/csv",
                "md5": md5_hash,
                "sha256": sha256_hash
            }
        ]
        
        metadata["recordSet"] = [
            {
                "@type": "cr:RecordSet",
                "@id": record_set_id,
                "name": record_set_id,
                "description": f"{csv_id.capitalize()} records",
                "field": []
            }
        ]
        
        # Add fields based on CSV headers
        for field_name in fieldnames:
            field_id = f"{record_set_id}/{field_name}"
            metadata["recordSet"][0]["field"].append({
                "@type": "cr:Field",
                "@id": field_id,
                "name": field_name,
                "description": f"{field_name} field",
                "dataType": "sc:Text",
                "source": {
                    "@type": "cr:ColumnSource",
                    "fileObject": csv_logical_name,
                    "column": field_name
                }
            })
        
        # If a temp JSON file path is provided, write the individual metadata to it
        if temp_json_file:
            self.temp_files.append(temp_json_file)
            with open(temp_json_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
        
        return metadata
    
    def read_edaschema_tables(self, directory: str, tables_only: bool = False, graph_tables_only: bool = False) -> List[str]:
        """
        Find all table.csv and/or graph_table.csv files in the specified directory and process them.
        
        Args:
            directory: The directory to search for table.csv and/or graph_table.csv files
            tables_only: If True, only process table.csv files
            graph_tables_only: If True, only process graph_table.csv files
            
        Returns:
            List of paths to processed table files
        """
        # Determine which files to include
        include_files = []
        if tables_only:
            include_files = ["table.csv"]
        elif graph_tables_only:
            include_files = ["graph_table.csv"]
        else:
            include_files = ["table.csv", "graph_table.csv"]
        
        # Find all matching files in the input directory (recursively)
        table_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file in include_files:
                    table_files.append(os.path.join(root, file))
        
        if not table_files:
            raise ValueError(f"No {', '.join(include_files)} files found in {directory}")
        
        # Process the found table files
        self.process_multiple_tables(table_files)
        
        return table_files
    
    def process_multiple_tables(self, table_files: List[str]) -> None:
        """
        Process multiple table files and combine their metadata.
        
        Args:
            table_files: List of paths to table.csv files
            
        Raises:
            ValueError: If no table files are provided
        """
        if not table_files:
            raise ValueError("No table files provided")
        
        # Initialize combined metadata
        self.metadata = dict(self.COMBINED_METADATA_TEMPLATE)
        # Set the date_published
        self.metadata["datePublished"] = self.date_published
        
        # Process each table file and add to combined metadata
        for table_file in table_files:
            # Create a temporary file to store the individual metadata
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
                tmp_path = tmp.name
                self.temp_files.append(tmp_path)
            
            # Read the table and get its metadata
            table_metadata = self.read_edaschema_table(table_file, tmp_path)
            
            # Add the distribution and recordSet to the combined metadata
            self.metadata["distribution"].extend(table_metadata["distribution"])
            self.metadata["recordSet"].extend(table_metadata["recordSet"])
    
    def write_croissant_file(self, filename: str) -> None:
        """
        Write the current metadata to a file in Croissant format.
        
        Args:
            filename: Path to the output JSON file
        """
        # Ensure the metadata is written in the correct order
        ordered_metadata = {}
        
        # First, add context and type
        ordered_metadata["@context"] = self.metadata["@context"]
        ordered_metadata["@type"] = self.metadata["@type"]
        
        # Then add dataset metadata fields
        for key in ["name", "description", "datePublished", "version", "license", 
                    "citation", "conformsTo", "url"]:
            if key in self.metadata:
                ordered_metadata[key] = self.metadata[key]
        
        # Finally add distribution and recordSet
        ordered_metadata["distribution"] = self.metadata["distribution"]
        ordered_metadata["recordSet"] = self.metadata["recordSet"]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(ordered_metadata, f, indent=2)
    
    def append_to_croissant_file(self, filename: str) -> None:
        """
        Append the current metadata to an existing Croissant file.
        If the file doesn't exist, it works like write_croissant_file.
        
        Args:
            filename: Path to the output JSON file
        """
        if not os.path.exists(filename):
            self.write_croissant_file(filename)
            return
        
        # Read existing file
        with open(filename, 'r', encoding='utf-8') as f:
            existing_metadata = json.load(f)
        
        # Append distributions and recordSets
        existing_metadata["distribution"].extend(self.metadata["distribution"])
        existing_metadata["recordSet"].extend(self.metadata["recordSet"])
        
        # Create ordered metadata
        ordered_metadata = {}
        
        # First, add context and type
        ordered_metadata["@context"] = existing_metadata["@context"]
        ordered_metadata["@type"] = existing_metadata["@type"]
        
        # Then add dataset metadata fields
        for key in ["name", "description", "datePublished", "version", "license", 
                    "citation", "conformsTo", "url"]:
            if key in existing_metadata:
                ordered_metadata[key] = existing_metadata[key]
        
        # Finally add distribution and recordSet
        ordered_metadata["distribution"] = existing_metadata["distribution"]
        ordered_metadata["recordSet"] = existing_metadata["recordSet"]
        
        # Write back the combined data
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(ordered_metadata, f, indent=2)
    
    def cleanup(self) -> None:
        """Clean up any temporary files created during processing."""
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        self.temp_files = []
    
    def __del__(self):
        """Destructor to ensure cleanup of temporary files."""
        self.cleanup()


def main():
    """Main function to parse arguments and process files."""
    parser = argparse.ArgumentParser(
        prog="DXLCroissant",
        description="Generate Croissant metadata JSON from EDASchema table file(s)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Create mutually exclusive group for input arguments
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--table', help='Input CSV file path')
    input_group.add_argument('--tables', nargs='+', help='Multiple table.csv files to process and combine (will replace existing output file unless --append is specified)')
    input_group.add_argument('--dir', help='Directory containing table.csv files to process')
    
    # Required output argument
    parser.add_argument('--croissant', required=True, help='Output Croissant JSON file path')
    parser.add_argument('--append', action='store_true', help='Append to existing Croissant file instead of overwriting')
    parser.add_argument('--date', help='Publication date in YYYY-MM-DD format (default: today\'s date)', 
                        default=date.today().isoformat())
    parser.add_argument('--tables-only', action='store_true', help='With --dir, only process table.csv files')
    parser.add_argument('--graph-tables-only', action='store_true', help='With --dir, only process graph_table.csv files')
    
    args = parser.parse_args()
    
    # Create DXLCroissant object with date
    croissant = DXLCroissant(date_published=args.date)
    
    try:
        if args.table:
            # Process a single table
            croissant.read_edaschema_table(args.table)
                
        elif args.tables:
            # Process multiple tables
            croissant.process_multiple_tables(args.tables)
        
        else:
            # Process all tables in a directory
            croissant.read_edaschema_tables(
                args.dir, 
                tables_only=args.tables_only,
                graph_tables_only=args.graph_tables_only
            )
        
        # Write or append to the output file
        if args.append:
            croissant.append_to_croissant_file(args.croissant)
        else:
            croissant.write_croissant_file(args.croissant)
    
    finally:
        # Clean up any temporary files
        croissant.cleanup()


if __name__ == "__main__":
    main()
