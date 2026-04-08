import sys
from pathlib import Path
sys.path.append("../../src/")

from datagen_graph import *

# This script demonstrates how users can perform data manipulation using SPARQL queries.
# It includes multiple examples that query an RDF graph based on the eda ontology, with specific tasks
# such as retrieving pin properties, counting pins per net, and filtering instances based on certain conditions.
# Users can specify the example to run via the command line (example 1 to 4).
#
# Example Usage:
#   python sparql_query_examples.py 1    # Run Example 1
#

def run_example(example_number, graph):
    """
    Run the specified example based on the example number.
    """
    if example_number == 1:
        example_1(graph)
    elif example_number == 2:
        example_2(graph)
    elif example_number == 3:
        example_3(graph)
    elif example_number == 4:
        example_4(graph)
    else:
        print(f"Example {example_number} is not a valid option.")

def example_1(graph):
    """
    Example 1: Retrieve first 5 Pins with Their Properties (pinX, pinY, setupFallArrival)
    """
    query = """
    
    SELECT ?pin ?pinName ?pinX ?pinY ?setupFallArrival
    WHERE {
        ?pin a eda:Pin .
        ?pin eda:pinName ?pinName .
        ?pin eda:pinX ?pinX .
        ?pin eda:pinY ?pinY .
        ?pin eda:setupFallArrival ?setupFallArrival .
    }

    LIMIT 5    
    """
    
    # Execute the query
    results = graph.query(query)
    
    for row in results:
        print(f"Pin: {row.pin}, PinName: {row.pinName}, PinX: {row.pinX}, PinY: {row.pinY}, setupFallArrival: {row.setupFallArrival}")

def example_2(graph):
    """
    Example 2: Get Nets with Their Length > value
    """
    query = """
    SELECT ?net ?netName ?netCapacitance ?netLength
    WHERE {
        ?net a eda:Net .
        ?net eda:netName ?netName .
        ?net eda:netLength ?netLength .
        FILTER (xsd:float(?netLength) > 20000)
    }
    ORDER BY ?netLength
    """

    # Execute the query
    results = graph.query(query)

    print("Example 2 Results: ")
    for row in results:
        print(f"Net: {row.net}, NetName: {row.netName}, Length: {row.netLength}")


def example_3(graph):
    """
    Example 3: Count the Number of Pins per Net, and return only for nets with pin count greater than 10.
    """

    query = """
    SELECT ?netName (COUNT(?pin) AS ?pinCount)
    WHERE {
        ?pin a eda:Pin .
        ?pin eda:netName ?netName .
    }
    GROUP BY ?netName
    HAVING (COUNT(?pin) > 10)
    """
    
    # Execute the query
    results = graph.query(query)
    
    for row in results:
        print(f"NetName: {row.netName}, PinCount: {row.pinCount}")

def example_4(graph):
    """
    Retrieve eda:libcellName for eda:Instance filtered by eda:is_seq = 1.
    """

    query = """
    SELECT DISTINCT ?libcellName
    WHERE {
        ?instance a eda:Instance .
        ?instance eda:is_seq "1"^^xsd:string .
        ?instance eda:libcellName ?libcellName .
    }
    """

    # Execute the query
    results = graph.query(query)

    print("Libcell Names for sequential instances:")
    for row in results:
        print(f"{row.libcellName}")

# Run the main function
if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    ontology_directory = script_dir.parents[4] / "ontology"
    croissant_directory = script_dir.parents[2] / "croissant"
    ontology_file = str(ontology_directory / "eda_ontology.ttl")
    metadata_file = str(croissant_directory / "circuitops_croissant_metadata_ontology.json")
    output_file = 'output_graph.ttl'  # Path to save the output RDF graph

    # Load the ontology and Croissant metadata
    graph = load_ontology(ontology_file)
    croissant_data = load_metadata(metadata_file)
    
    # Convert the Croissant metadata into an RDF graph
    graph = convert_croissant_to_rdf(croissant_data, graph)
    
    example = sys.argv[1]

    run_example(int(example), graph)
