import rdflib
import json, os
import pandas as pd
import grpc
from io import StringIO
from pathlib import Path
import data_service_pb2
import data_service_pb2_grpc
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, BNode
from rdflib.collection import Collection

# Function to load the ontology file into a graph
def load_ontology(ontology_file):
    graph = rdflib.Graph()
    graph.parse(ontology_file, format='turtle')
    return graph

# Function to load the Croissant metadata JSON file
def load_metadata(croissant_file):
    with open(croissant_file, 'r') as file:
        return json.load(file)

# Function to get field mappings for a specific record set in the Croissant metadata
def get_field_mappings(croissant_data, recordset_id):
    # Find the recordset by ID
    properties_recordset = next(item for item in croissant_data['recordSet'] if item['@id'] == recordset_id)
    
    # Extract field mappings
    field_mappings = {}
    for field in properties_recordset['field']:
        field_mappings[field['name']] = field['source']['extract']['column']
    
    return field_mappings, properties_recordset

# Function to process the CSV and convert it into RDF triples
def process_csv_to_rdf(croissant_data, recordset_id, graph):
    # Get file location and field mappings
    file_info = next(item for item in croissant_data['distribution'] if item['@id'] == recordset_id)
    csv_location = file_info['contentUrl']
    
    # Porperty to entity id map
    #map_file = {"net_properties" : "Net", "pin_properties" : "Pin", "inst_properties" : "Inst"}

    # Get field mappings for the recordset
    field_mappings, _ = get_field_mappings(croissant_data, recordset_id)
    
    # Read the CSV into a DataFrame
    df = pd.read_csv(csv_location)
    
    #if recordset_id in map_file:
    #    entity_id = map_file[recordset_id]
    #else:
    #    return graph

    entity_id = recordset_id

    # Iterate through the DataFrame and create RDF triples
    for index, row in df.iterrows():
        entity_uri = rdflib.URIRef(f"http://example.org/eda/{entity_id}_{index}")
        
        # Add the class type for the entity (based on recordset type)
        graph.add((entity_uri, rdflib.RDF.type, rdflib.URIRef(f"http://example.org/eda#{entity_id}")))

        # Add properties based on the field mappings
        for field_name, csv_column in field_mappings.items():
            ontology_property_uri = rdflib.URIRef(f"http://example.org/eda#{field_name}")
            
            csv_value = row[csv_column]
            
            # Add the property as a literal with appropriate datatype
            if isinstance(csv_value, bool):
                graph.add((entity_uri, ontology_property_uri, rdflib.Literal(csv_value, datatype=rdflib.XSD.boolean)))
            elif isinstance(csv_value, float):
                graph.add((entity_uri, ontology_property_uri, rdflib.Literal(csv_value, datatype=rdflib.XSD.float)))
            else:
                graph.add((entity_uri, ontology_property_uri, rdflib.Literal(csv_value, datatype=rdflib.XSD.string)))
    
    return graph

# Function to iterate through all the files in the Croissant metadata and convert them to RDF
def convert_croissant_to_rdf(croissant_data, graph):
    for file_info in croissant_data['distribution']:
        recordset_id = file_info['@id']
        print(recordset_id)
        
        # Process each random_forest_inforecord set and update the graph
        graph = process_csv_to_rdf(croissant_data, recordset_id, graph)
    
    return graph

# Function to extract specific properties from the graph and return a sub graph
def get_filtered_rdf_graph(properties, graph):
    # Create a new RDF graph to store the filtered triples
    filtered_graph = rdflib.Graph()
    
    property_instances = {}

    for prop in properties:
        # Create the URIRef for the property (to match it in the graph)
        property_uri = rdflib.URIRef(f"http://example.org/eda#{prop}")
        
        # SPARQL query to get all instances of the property
        query = """
        SELECT ?subject ?value WHERE {
            ?subject <""" + str(property_uri) + """> ?value .
        }
        """
        
        # Execute the query
        results = graph.query(query)
        
        # Store the results in the dictionary for this property
        for row in results:
            filtered_graph.add((row[0], property_uri, row[1]))
    
    return filtered_graph

# Main function to tie everything together
def main(ontology_file, croissant_file, output_file):
    # Load the ontology and Croissant metadata
    graph = load_ontology(ontology_file)
    croissant_data = load_metadata(croissant_file)
    
    # Convert the Croissant metadata into an RDF graph
    graph = convert_croissant_to_rdf(croissant_data, graph)
    
    # Save the RDF graph to an output file
    graph.serialize(destination=output_file, format='turtle')
    print(f"RDF graph saved to {output_file}")

    properties = ["pinName", "loadCapacitance", "netCapacitance", "netLength", "setupRiseArrival", "setupFallArrival", "pinX", "pinY"]
    filtered_graph = get_filtered_rdf_graph(properties, graph)

    filtered_graph.serialize(destination="fil_graph.ttl", format='turtle')


# Run the main function
if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    ontology_directory = script_dir.parents[4] / "ontology"
    croissant_directory = script_dir.parent / "croissant"
    ontology_file = ontology_directory / "eda_ontology.ttl"
    metadata_file = croissant_directory / "circuitops_croissant_metadata_ontology.json"
    output_file = 'output_graph.ttl'  # Path to save the output RDF graph

    main(str(ontology_file), str(metadata_file), output_file)
