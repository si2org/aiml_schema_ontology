#!/usr/bin/env python
# coding: utf-8
# SPDX-FileCopyrightText: Copyright (c) 2022 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import numpy as np
import pandas as pd
import torch
import dgl
from rdflib import Graph, URIRef


def rdf_graph_to_dataframe(graph):
    """
    Converts RDF graph into a pandas DataFrame.
    """
    data = []
    for subject, predicate, obj in graph:
        data.append({
            "subject": str(subject),
            "predicate": str(predicate),
            "object": str(obj)
        })
    return pd.DataFrame(data)


def extract_node_features(node_df, pin_to_node_id):
    """
    Construct node features such as pinX, pinY, direction.
    """
    pin_properties = ['pinX', 'pinY', 'direction']
    node_features = {prop: [] for prop in pin_properties}

    # Extract properties for each pin (pinX, pinY, is_port, direction)
    for prop in pin_properties:
        feature_values = node_df[node_df['predicate'] == f'http://example.org/eda#{prop}']['object'].values
        
        if prop == 'direction':
            feature_values = np.array([True if val.lower() == 'true' else False for val in feature_values])
        
        node_features[prop] = feature_values

    # Map the properties to the nodes using pin_to_node_id
    node_feature_array = np.stack([node_features['pinX'], node_features['pinY'], node_features['direction']], axis=1)

    # Map the node features based on pinName
    # Ensure the order of features matches the pin names in the graph (matching pin_name to node_id)
    feature_array_for_nodes = []
    for pin_name, node_id in pin_to_node_id.items():
        feature_array_for_nodes.append(node_feature_array[node_id])

    return node_feature_array.astype(np.float32)

def extract_edge_features(edge_df):
    """
    Construct edge features such as delayValue and edge type.
    """
    # Extract edge features like delayValue, libcellname for cell edges, and netCap, netResonance, netLength for net edges
    delay_values = edge_df[edge_df['predicate'] == 'http://example.org/eda#delayValue']['object'].values.astype(float)

    # For cell edges, extract libcellname; for net edges, extract netCap, netResonance, netLength
    libcellnames = edge_df[edge_df['predicate'] == 'http://example.org/eda#libcellName']['object'].values
    net_caps = edge_df[edge_df['predicate'] == 'http://example.org/eda#netCapacitance']['object'].values.astype(float)
    net_res = edge_df[edge_df['predicate'] == 'http://example.org/eda#netResistance']['object'].values.astype(float)
    net_length = edge_df[edge_df['predicate'] == 'http://example.org/eda#netLength']['object'].values.astype(float)


    # Return edge features as a dictionary (cell and net edge features)
    return {
        'delay_values': delay_values,
        'libcellnames': libcellnames,
        'net_caps': net_caps,
        'net_res': net_res,
        'net_length': net_length
    } 


def construct_dgl_graph_from_rdf(filtered_graph):
    """
    Construct the DGL graph from the filtered RDF data, including nodes and edges.
    """
    # Convert the filtered RDF graph into DataFrame
    node_df = rdf_graph_to_dataframe(filtered_graph)
    edge_df = rdf_graph_to_dataframe(filtered_graph)

    # Extract unique nodes from sourcePinName and sinkPinName
    source_pins = edge_df[edge_df['predicate'] == 'http://example.org/eda#sourcePinName']['object'].values
    sink_pins = edge_df[edge_df['predicate'] == 'http://example.org/eda#sinkPinName']['object'].values

    # Create unique pin names as nodes
    unique_pins = set(source_pins).union(set(sink_pins))

    # Create a mapping of pin name to node ID
    pin_to_node_id = {pin: idx for idx, pin in enumerate(unique_pins)}

    # Extract node features (pinX, pinY, is_port, direction) and match to node IDs
    node_features = extract_node_features(node_df, pin_to_node_id)
    node_features = node_features[:len(unique_pins)]

    # Extract edge features (delayValue, libcellname for cell edges, netCap, netResonance, netLength for net edges)
    edge_features = extract_edge_features(edge_df)

    # Create edges between sourcePinName and sinkPinName
    src_ids = [pin_to_node_id[pin] for pin in source_pins]
    dst_ids = [pin_to_node_id[pin] for pin in sink_pins]
    delay_values = list(edge_features['delay_values'])
    delay_values = delay_values[:len(unique_pins)]
    

    # Create edge types: 'cell_out' (edgeType = 0) or 'net_out' (edgeType = 1)
    edge_type_dict = {'0': 'cell_out', '1': 'net_out'}

    # Create the heterograph (DGL graph) with edge types
    data_dict = {
        ('node', 'cell_out', 'node'): (torch.tensor(src_ids), torch.tensor(dst_ids)),
        ('node', 'net_out', 'node'): (torch.tensor(dst_ids), torch.tensor(src_ids)),
    }

    g = dgl.heterograph(data_dict)

    # Add node features to the graph (merging the properties with the correct pin ID)
    g.ndata['nf'] = torch.tensor(node_features)
    g.ndata['delay'] = torch.tensor(delay_values)

    #task_targets = ['pinSlew', 'pinSlack', 'pinRiseArrival', 'pinFallArrival']
    #for task_target in task_targets:
    #    g.ndata[f'{task_target}'] = torch.from_numpy([])
    
    # Add additional edge features based on edge type
    libcellnames = edge_features['libcellnames']
    net_caps = edge_features['net_caps']
    net_res = edge_features['net_res']
    net_length = edge_features['net_length']

    # Adding cell_edge and net_edge features
    libcellname_to_id = {libcell: idx for idx, libcell in enumerate(set(libcellnames))}
    # Map the libcellnames in the input list to their corresponding IDs
    libcell_ids = [libcellname_to_id[libcell] for libcell in libcellnames]

    num_edges = g.num_edges(('node', 'cell_out', 'node'))
    
    padding = np.zeros(num_edges - len(libcell_ids))
    libcell_ids = np.concatenate([libcell_ids, padding])
    padding = np.zeros(num_edges - len(net_caps))
    net_caps = np.concatenate([net_caps, padding])
    padding = np.zeros(num_edges - len(net_res))
    net_res = np.concatenate([net_res, padding])
    padding = np.zeros(num_edges - len(net_length))
    net_length = np.concatenate([net_length, padding])
    

    # Add edge features : LUT and net props to graph
    g.edata['ef'] = {
        ('node', 'cell_out', 'node'): torch.tensor(libcell_ids),
        ('node', 'net_out', 'node'): torch.stack([torch.tensor(net_caps), torch.tensor(net_res), torch.tensor(net_length)], dim=1)
    }

    return g

def construct_dgl_main(filtered_graph, data_dir):
    """
    Main function to preprocess and construct the DGL graph from filtered RDF data.
    """
    # Construct the DGL graph from the filtered RDF graph
    g = construct_dgl_graph_from_rdf(filtered_graph)

    # Save the DGL graph
    dgl.save_graphs(f'{data_dir}/graph.dgl', [g])

    print("Graph construction complete!")


# Sample Usage

if __name__ == "__main__":
    # Load RDF Graph
    graph = Graph()
    graph.parse("eda_ontology.ttl", format="turtle")  # Path to your RDF ontology file

    # Define the required properties
    required_properties = ['pinName', 'netName', 'pinX', 'pinY', 'direction', 'sourcePinName', 'sinkPinName', 'edgeType', 'delayValue']

    # Extract the filtered RDF graph with all necessary properties using SPARQL
    filtered_graph = extract_properties_with_sparql(required_properties, graph)

    # Define the data directory where you want to save the DGL graph
    data_dir = "./data"  # Your data directory

    # Construct and save the DGL graph
    construct_dgl_main(filtered_graph, data_dir)

