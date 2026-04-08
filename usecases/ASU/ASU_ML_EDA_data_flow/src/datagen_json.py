import json
import pandas as pd
import importlib
import os
import grpc
from io import StringIO
import data_service_pb2
import data_service_pb2_grpc

# Establish gRPC connection
channel = grpc.insecure_channel('localhost:50051')
stub = data_service_pb2_grpc.DataServiceStub(channel)

# Read taxonomy file
def load_taxonomy(taxonomy_path):
    with open(taxonomy_path, "r") as f:
        return json.load(f)

# Read croissant file
def load_metadata(metadata_path):
    with open(metadata_path, "r") as f:
        return json.load(f)

# Function to raise a gRPC request
def request_file_from_grpc(file_path):
    """Request a file from the gRPC server and reconstruct it."""
    request = data_service_pb2.FileRequest(file_path=file_path)
    file_content = ""

    for chunk in stub.GetFile(request):
        file_content += chunk.content.decode("utf-8")
    
    return StringIO(file_content)


def get_primary_id(entity):
    global taxonomy

    e = taxonomy[entity]
    prime_id = e["properties"][0]["name"]

    return prime_id

# Find parent entity
def find_parent_entities(entity):
    """Find parent entities dynamically by checking where this entity appears in 'has' relationships."""
    global taxonomy
    parents = []
    for parent_entity, attributes in taxonomy.items():
        if "has" in attributes and entity in attributes["has"].values():
            parents.append(parent_entity)
    return parents

# Parses the croissant file and finds the datasource
def find_relevant_datasets(metadata, features):
    relevant_files = {}
    column_map = {}

    for record in metadata["recordSet"]:
        for field in record["field"]:
            field_name = field["name"]
            if field_name in features:
                file_id = field["source"]["fileObject"]["@id"]
                column = field["source"]["extract"]["column"]
                column_map[field_name] = column
                file_entry = next((f for f in metadata["distribution"] if f["@id"] == file_id), None)
                if file_entry:
                    relevant_files[field_name] = file_entry["contentUrl"]
    
    return relevant_files, column_map

# Reads the necessary files and extracts the columns
def load_and_merge_data(relevant_files, column_map, prime_id):
    dataset = pd.DataFrame()
    files = set(relevant_files.values())

    get_from_server = 0

    for file in files:
        if (get_from_server):
            try:
                # Request file from gRPC server
                file_obj = request_file_from_grpc(file)
                df = pd.read_csv(file_obj)
            except Exception as e:
                print(f"Error retrieving file {file} from gRPC: {e}")
                continue
        else:
            if os.path.exists(file):
                df = pd.read_csv(file)
            else:
                print("Error: File ",file,"not found")
                continue
        for k in relevant_files.keys():
            if relevant_files[k] == file:
                dataset[k] = df[column_map[k]]
        if prime_id != None and prime_id not in dataset.columns:
            dataset[prime_id] = df[prime_id]
    
    return dataset

def find_property_source(entity, property_name):
    global taxonomy

    # Check parent entities
    parent_entities = find_parent_entities(entity)
    for parent in parent_entities:
        if property_name in [prop["name"] for prop in taxonomy[parent].get("properties", [])]:
            return parent, get_primary_id(parent)

    # Check child entities (directly defined in "has")
    for child, child_entity in taxonomy[entity].get("has", {}).items():
        if property_name in [prop["name"] for prop in taxonomy[child_entity].get("properties", [])]:
            return child_entity, get_primary_id(child_entity)

    return None, None  # Property not found

def get_properties_dataset(entity, properties):
    global metadata
    global taxonomy

    if entity == None:
    # Find relevant dataset files
        relevant_files, column_map = find_relevant_datasets(metadata, properties)
        print("Relevant Data Files:", relevant_files)
        print("Column map:", column_map)
        print('\n')
        
        # Load and process dataset
        dataset = load_and_merge_data(relevant_files, column_map, None)
        return dataset
    
    entity_primary_key = get_primary_id(entity)
    dataset = pd.DataFrame()
    
    # Maps the source entity for all the requested properties
    property_map = {}
    for prop in properties:
        if prop in [prop1["name"] for prop1 in taxonomy[entity].get("properties", [])]:
            if entity in property_map.keys():
                property_map[entity]["properties"].append(prop)
            else:
                property_map[entity] = {}
                property_map[entity]["properties"] = []
                property_map[entity]["properties"].append(prop)
                property_map[entity]["prime_id"] = entity_primary_key
        else:
            actual_entity, merge_key = find_property_source(entity, prop)
            if actual_entity == None:
                continue
            if actual_entity in property_map.keys():
                property_map[actual_entity]["properties"].append(prop)
            else:
                property_map[actual_entity] = {}
                property_map[actual_entity]["properties"] = []
                property_map[actual_entity]["properties"].append(prop)
                property_map[actual_entity]["prime_id"] = merge_key

    entity_ids = [x["prime_id"] for x in property_map.values()]

    relevant_files, column_map = find_relevant_datasets(metadata, property_map[entity]['properties']+entity_ids)
    dataset = load_and_merge_data(relevant_files, column_map, property_map[entity]['prime_id'])
    
    # Merges the properties of entities other than primary using merge_key
    for e in property_map.keys():
        if e==entity:
            continue
        relevant_files, column_map = find_relevant_datasets(metadata, property_map[e]['properties'])
        temp_df = load_and_merge_data(relevant_files, column_map, property_map[e]['prime_id'])
        dataset = dataset.merge(temp_df, left_on=property_map[e]['prime_id'], right_on=property_map[e]['prime_id'], how="left")
    dataset = dataset.drop_duplicates(subset=[property_map[entity]['prime_id']])
    return dataset

def get_graph(graph_type, graph_features):
    global taxonomy
    global metadata

    tg = taxonomy[graph_type]
    nodes = tg['nodes']
    edges = tg ['edges']
    

    graph_df = pd.DataFrame()
    #graph_df = pd.DataFrame(columns=node_types)
    for edge in edges:
        edge_entity = taxonomy[edge]
        edge_properties = edge_entity['properties']
        edge_properties = [x['name'] for x in edge_properties]
        node_entity_types = list(edge_entity["has"].values())
        node_types = list(edge_entity["has"].keys())

        if "are" in edge_entity.keys():
            edge_types = edge_entity["are"]
        else:
            edge_types = []

        temp_df = get_properties_dataset(None, node_types)
        graph_df = pd.concat([graph_df, temp_df], axis=0, ignore_index=True)
        
        for i,node in enumerate(node_types):
            node_entity_type = node_entity_types[i]
            prime_id = get_primary_id(node_entity_type)
            node_features = graph_features[node]
            node_df = get_properties_dataset(node_entity_type, node_features)

            rename_dict = {col: f"{node}_{col}" for col in node_df.columns if col != prime_id}
            node_df = node_df.rename(columns=rename_dict)

            graph_df = graph_df.merge(node_df, left_on=node, right_on=prime_id, how="left")
            graph_df.drop(columns=[prime_id], inplace=True)
            
    temp_df = get_properties_dataset(None, edge_properties)
    #print("here",temp_df.columns)
    graph_df = pd.concat([graph_df, temp_df], axis=1)
    
    return graph_df

def preprocess_dataset(pin_graph_dataset):

    pin_graph_dataset = pin_graph_dataset[pin_graph_dataset['edge_type']==0]

    return pin_graph_dataset
    
# Main Execution
if __name__ == "__main__":

    schema_directory = "../../../../ontology/"
    taxonomy_file = schema_directory+"taxonomy_v0p5.json"
    metadata_file = schema_directory+"circuitops_croissant_metadata.json"
    pb2_module = ""

    # Load files
    taxonomy = load_taxonomy(taxonomy_file)
    metadata = load_metadata(metadata_file)
    #grpc_fields = load_grpc_fields(PB2_MODULE)

    # Set required fields
    # Arc delay predictor
    driver_features = ["pin_name", "worst_slew", "libcell_name"]
    sink_features = ["pin_name", "load_capacitance"]

    # Net delay predictor
    #driver_features = ["pin_name", "load_capacitance", "pin_x", "pin_y"]
    #sink_features = ["pin_name", "input_capacitance", "pin_x", "pin_y"]

    graph_features = {"driver_pin" : driver_features, "sink_pin" : sink_features}

    print("Features:", graph_features)
    print('\n')

    
    #features_dataset = get_properties_dataset("Pin", features)
    pin_graph_dataset = get_graph("TimingGraph", graph_features)
    
    final_dataset = preprocess_dataset(pin_graph_dataset)
    print(final_dataset)
