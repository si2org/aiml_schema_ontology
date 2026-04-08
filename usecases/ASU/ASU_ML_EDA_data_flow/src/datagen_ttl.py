import rdflib
import json, os
from pathlib import Path
import pandas as pd
import grpc
from io import StringIO
import data_service_pb2
import data_service_pb2_grpc
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, BNode
from rdflib.collection import Collection

# Establish gRPC connection
channel = grpc.insecure_channel('localhost:50051')
stub = data_service_pb2_grpc.DataServiceStub(channel)

# Define namespace
EDA = Namespace("http://example.org/eda#")

# Default fallback mapping for primary IDs when the ontology omits eda:primaryId annotations
DEFAULT_PRIMARY_IDS = {
    str(EDA.sourceNode): "sourcePinName",
    str(EDA.sinkNode): "sinkPinName",
}

# Loading Ontologies
def load_ontologies(ontology_paths):
    """Parse one or more Turtle ontology files into a single RDF graph."""
    g = rdflib.Graph()
    for path in ontology_paths:
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Ontology file not found: {path_obj}")
        g.parse(str(path_obj), format="turtle")
    return g

# Read croissant file
def load_metadata(metadata_path):
    metadata_path = Path(metadata_path)
    with metadata_path.open("r") as f:
        return json.load(f)

# Function to raise a gRPC request
def request_file_from_grpc(file_path):
    request = data_service_pb2.FileRequest(file_path=file_path)
    file_content = ""
    for chunk in stub.GetFile(request):
        file_content += chunk.content.decode("utf-8")
    return StringIO(file_content)

# Function to use RDF to find parents of an entity
def find_parent_entities(g, child_entity_uri):
    parents = []
    for oprop in g.subjects(RDF.type, OWL.ObjectProperty):
        for rng in g.objects(oprop, RDFS.range):
            if rng == child_entity_uri:
                for domain in g.objects(oprop, RDFS.domain):
                    parents.append(domain)
    return parents

# Function to use RDF to find children of an entity
def find_child_entities(g, child_entity_uri):
    parents = []
    for oprop in g.subjects(RDF.type, OWL.ObjectProperty):
        for rng in g.objects(oprop, RDFS.domain):
            if rng == child_entity_uri:
                for domain in g.objects(oprop, RDFS.range):
                    parents.append(domain)
    return parents

# Parses the croissant file and finds the datasource
def find_relevant_datasets(metadata, features,metadata_file,prime_id=None):
    relevant_files = {}
    column_map = {}
    records = []
    if prime_id != None:
        for record in metadata["recordSet"]:
            for field in record["field"]:
                field_name = field["name"]
                if field_name == prime_id:
                    file_id = field["source"]["fileObject"]["@id"]
                    records.append(record)
        for record in records:
            for field in record["field"]:
                field_name = field["name"]
                if field_name in features:
                    file_id = field["source"]["fileObject"]["@id"]
                    column = field["source"]["extract"]["column"]
                    column_map[field_name] = column
                    file_entry = next((f for f in metadata["distribution"] if f["@id"] == file_id), None)
                    file_entry_abs = str(metadata_file.parent)+'/'+ file_entry["contentUrl"]
                    if file_entry:
                        #relevant_files[field_name] = file_entry["contentUrl"] #updating to get data from local path
                        relevant_files[field_name] = file_entry_abs
    else:
        for record in metadata["recordSet"]:
            for field in record["field"]:
                field_name = field["name"]
                if field_name in features:
                    file_id = field["source"]["fileObject"]["@id"]
                    column = field["source"]["extract"]["column"]
                    column_map[field_name] = column
                    file_entry = next((f for f in metadata["distribution"] if f["@id"] == file_id), None)
                    if file_entry:
                        file_entry_abs = str(metadata_file.parent)+'/'+ file_entry["contentUrl"] #updating to get data from local path
                        relevant_files[field_name] = file_entry_abs
    return relevant_files, column_map

#this is based on recordSet fileObject @id = distrbution @id 
def find_relevant_column(metadata, prime_id, file_name):
    # Map fileObject @id -> file name
    file_id_to_name = {
        f["@id"]: f.get("name")
        for f in metadata.get("distribution", [])
    }

    for record in metadata.get("recordSet", []):
        for field in record.get("field", []):
            if field.get("name") != prime_id:
                continue
            file_id = field["source"]["fileObject"]["@id"]
            if file_id_to_name.get(file_id) == file_name:
                return field["source"]["extract"]["column"]

    raise ValueError(
        f"No column found for prime_id={prime_id} in file={file_name}"
    )


# Function to get union of classes as list
def extract_union_classes(g, bnode):
    union = g.value(bnode, OWL.unionOf)
    return [c for c in Collection(g, union)] if union else []


def resolve_primary_id(graph, resource):
    """Return the primary ID fragment for a resource, falling back to defaults."""
    if resource is None:
        return None
    primary = graph.value(resource, EDA.primaryId)
    if primary:
        return primary.split('#')[-1]
    fallback = DEFAULT_PRIMARY_IDS.get(str(resource))
    resource_name = str(resource).split("#")[-1]
    if fallback:
        print(
            f"Error: No eda:primaryId annotation found for {resource_name}; "
            f"falling back to default identifier '{fallback}'."
        )
    else:
        print(
            f"Error: Unable to determine primary ID for {resource_name}; "
            "dataset joins depending on this identifier will likely fail."
        )
    return fallback


# Reads the necessary files and extracts the columns
def load_and_merge_data(metadata, relevant_files, column_map, prime_id):
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
                print(f"Error: File  {file} (from metadata entry {file}) not found")
                continue

        for k in relevant_files.keys():
            if relevant_files[k] == file and k != prime_id:
                dataset[k] = df[column_map[k]]
        if prime_id is not None and prime_id not in dataset.columns:
            file_name = file.split('/')[-1]
            prime_id_column = find_relevant_column(metadata, prime_id, file_name)
            dataset[prime_id] = df[prime_id_column]
    return dataset

# Function to get the datatype properties for an entity and also include the unionOf nodes
def _domain_includes_class(graph, domain_value, cls):
    if domain_value == cls:
        return True
    if isinstance(domain_value, BNode):
        union = graph.value(domain_value, OWL.unionOf)
        if union:
            for member in Collection(graph, union):
                if member == cls:
                    return True
    return False


def get_class_props(graph, cls):
    props = []
    for prop in graph.subjects(RDF.type, OWL.DatatypeProperty):
        domains = list(graph.objects(prop, RDFS.domain))
        if not domains:
            continue
        for domain_value in domains:
            if _domain_includes_class(graph, domain_value, cls):
                range_ = graph.value(prop, RDFS.range)
                if range_:
                    prop_label = prop.split("#")[-1]
                    props.append(prop_label)
                break
    return props

# Find source entity for a given property
def find_property_source(graph, entity_uri, property_name):

    # Check parent entities
    parents = find_parent_entities(graph, entity_uri)
    for parent_uri in parents:
        parent_props = get_class_props(graph, parent_uri)
        if property_name in parent_props:
            primary_id = resolve_primary_id(graph, parent_uri)
            return parent_uri, primary_id

    # Check children entities
    children = find_child_entities(graph, entity_uri)
    for child_uri in children:
        child_props = get_class_props(graph, child_uri)
        if property_name in child_props:
            primary_id = resolve_primary_id(graph, child_uri)
            return child_uri, primary_id

    return None, None

# Function to form a dataset with given properties
def get_properties_dataset(g, metadata, entity, properties, metadata_file):

    if entity == None:
    # Find relevant dataset files
        relevant_files, column_map = find_relevant_datasets(metadata, properties, metadata_file)
        #print("Relevant Data Files:", relevant_files) #cause testing issues w.r.t to file abs path
        print("Column map:", column_map)
        print('\n')
        
        # Load and process dataset
        dataset = load_and_merge_data(metadata, relevant_files, column_map, None)
        return dataset
    
    entity_primary_key = resolve_primary_id(g, entity)
    if entity_primary_key is None:
        raise ValueError(f"Unable to resolve primary ID for entity {entity}. "
                         "Update the ontology to include eda:primaryId or extend DEFAULT_PRIMARY_IDS.")
    dataset = pd.DataFrame()
    
    # Maps the source entity for all the requested properties
    property_map = {}
    main_entity_properties = get_class_props(g, entity)
    for prop in properties:
        if prop in main_entity_properties:
            if entity in property_map.keys():
                property_map[entity]["properties"].append(prop)
            else:
                property_map[entity] = {}
                property_map[entity]["properties"] = []
                property_map[entity]["properties"].append(prop)
                property_map[entity]["prime_id"] = entity_primary_key
        else:
            actual_entity, merge_key = find_property_source(g, entity, prop)
            if actual_entity == None:
                continue
            if merge_key is None:
                raise ValueError(f"Unable to resolve primary ID for related entity {actual_entity} "
                                 f"while retrieving property '{prop}'.")
            if actual_entity in property_map.keys():
                property_map[actual_entity]["properties"].append(prop)
            else:
                property_map[actual_entity] = {}
                property_map[actual_entity]["properties"] = []
                property_map[actual_entity]["properties"].append(prop)
                property_map[actual_entity]["prime_id"] = merge_key

    entity_ids = [x["prime_id"] for x in property_map.values()]
    relevant_files, column_map = find_relevant_datasets(metadata, property_map[entity]['properties']+entity_ids, metadata_file)
    dataset = load_and_merge_data(metadata, relevant_files, column_map, property_map[entity]['prime_id'])
    # Merges the properties of entities other than primary using merge_key
    for e in property_map.keys():
        if e==entity:
            continue
        relevant_files, column_map = find_relevant_datasets(metadata, property_map[e]['properties'], metadata_file, property_map[e]['prime_id'])
        temp_df = load_and_merge_data(metadata, relevant_files, column_map, property_map[e]['prime_id'])
        dataset = dataset.merge(temp_df, left_on=property_map[e]['prime_id'], right_on=property_map[e]['prime_id'], how="left")
    dataset = dataset.drop_duplicates(subset=[property_map[entity]['prime_id']])
    return dataset


def get_graph(g, graph_type_uri, graph_features, metadata, metadata_file):
    global EDA
    
    if (g.value(EDA.hasNode, RDFS.domain) == graph_type_uri):
        node = list(g.triples((EDA.hasNode, RDFS.range, None)))[0][2]
        class_type = list(g.triples((EDA.represents, RDFS.range, None)))[0][2]
        if isinstance(class_type, BNode) and (class_type, OWL.unionOf, None) in g:
            class_type = extract_union_classes(g, class_type)
    if (g.value(EDA.hasEdge, RDFS.domain) == graph_type_uri):
        edge = list(g.triples((EDA.hasEdge, RDFS.range, None)))[0][2]
        edge_properties = get_class_props(g, edge)

    main_class_types = [list(g.triples((x, RDFS.subClassOf, None)))[0][2] for x in class_type]
    class_type = main_class_types[0]
    
    graph_df = pd.DataFrame()
     
    node_types = []
    # get node types in given graph
    for s in g.subjects(RDF.type, OWL.ObjectProperty):
        domain = g.value(s, RDFS.domain)
        range_ = g.value(s, RDFS.range)
        if domain == edge and range_ == node:
            node_types.append(s)
    
    node_type_ids = []
    for sn in node_types:
        primary_id = resolve_primary_id(g, sn)
        if primary_id is None:
            raise ValueError(
                f"Unable to resolve primary ID for node type {sn}. "
                "Ensure the ontology annotates the object property with eda:primaryId "
                "or extend DEFAULT_PRIMARY_IDS."
            )
        node_type_ids.append(primary_id)
    temp_df = get_properties_dataset(g, metadata, None, node_type_ids,metadata_file)
    graph_df = pd.concat([graph_df, temp_df], axis=0, ignore_index=True)
    # Get the properties for each node type
    for i, node_type in enumerate(node_types):
        prime_id = resolve_primary_id(g, class_type)
        if prime_id is None:
            raise ValueError(
                "Unable to resolve primary ID for class type "
                f"{class_type}. Update the ontology or extend DEFAULT_PRIMARY_IDS."
            )
        node_type_name = node_type.split('#')[-1]
        node_type_id = node_type_ids[i]
        if node_type_name not in graph_features:
            raise KeyError(
                f"Graph features missing configuration for '{node_type_name}'. "
                f"Available keys: {list(graph_features.keys())}"
            )
        node_features = graph_features[node_type_name]
        node_df = get_properties_dataset(g, metadata, class_type, node_features, metadata_file)
        rename_dict = {col: f"{node_type_name}_{col}" for col in node_df.columns if col != prime_id}
        node_df = node_df.rename(columns=rename_dict)

        graph_df = graph_df.merge(node_df, left_on=node_type_id, right_on=prime_id, how="left")
        graph_df.drop(columns=[prime_id], inplace=True)

    temp_df = get_properties_dataset(g, metadata, None, edge_properties, metadata_file)
    graph_df = pd.concat([graph_df, temp_df], axis=1)

    return graph_df

def preprocess_dataset(pin_graph_dataset):
    if 'edgeType' not in pin_graph_dataset.columns:
        print("Error: 'edgeType' column not present in dataset; skipping driver/sink filtering.")
        return pin_graph_dataset
    pin_graph_dataset = pin_graph_dataset[pin_graph_dataset['edgeType'] == 0]
    return pin_graph_dataset

# Main Execution
if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent #getting the file directory
    schema_directory = script_dir.parent.parent.parent.parent / "ontology"  #getting the schema directory
    croissant_directory = script_dir.parent / "croissant"
    # To include adapter ontology file along with core ontology
    ontology_files = [
        schema_directory / "eda_ontology.ttl",
        schema_directory / "eda-ontology-adapter.ttl",
    ]
    metadata_file = croissant_directory / "circuitops_croissant_metadata_ontology_modified.json"

    # Load Ontology and Metadata
    graph = load_ontologies(ontology_files)
    metadata = load_metadata(str(metadata_file))
    
    # Arc delay predictor
    driver_features = ["pinName", "worstSlew", "libcellName"]
    sink_features = ["pinName", "loadCapacitance"]
    
    # Define Graph Features
    #driver_features = ["pinName", "loadCapacitance", "netCapacitance", "netLength", "setupRiseArrival", "setupFallArrival", "pinX", "pinY"]
    #sink_features = ["pinName", "inputCapacitance", "setupRiseArrival", "setupFallArrival", "pinX", "pinY"]

    graph_features = {
        "sourceNode": driver_features,
        "sinkNode": sink_features
    }

    print("Features:", graph_features)
    print('\n')

    # Dataset Generation
    timing_graph_uri = EDA.TimingGraph 
    pin_graph_dataset = get_graph(graph, timing_graph_uri, graph_features, metadata, metadata_file)

    final_dataset = preprocess_dataset(pin_graph_dataset)

    print(final_dataset)
