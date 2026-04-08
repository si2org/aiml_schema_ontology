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

import os, sys
from pathlib import Path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))+"/../"
sys.path.append(ROOT_DIR)
sys.path.append("../../src/")

import numpy as np
import pandas as pd
import pickle as pk
import graph_tool as gt
import matplotlib.pyplot as plt

from datagen_graph import *

from construct_dgl import *
from preprocess_dgl_graph import *
from train_gnn import *
from model import TimingGCN

if __name__ == "__main__":

    # Set Schema path
    script_dir = Path(__file__).resolve().parent
    ontology_directory = script_dir.parents[4] / "ontology"
    croissant_directory = script_dir.parents[2] / "croissant"
    ontology_file = str(ontology_directory / "eda_ontology.ttl")
    metadata_file = str(croissant_directory / "circuitops_croissant_metadata_ontology.json")

    # Load Ontology and Metadata
    graph = load_ontology(ontology_file)
    metadata = load_metadata(metadata_file)

    # Convert data source into RDF graph
    graph = convert_croissant_to_rdf(metadata, graph)

    properties = ['pinName', 'netName', 'netResistance', 'netCapacitance', 'netLength', 'libcellName', 'pinX', 'pinY', 'direction', 'sourcePinName', 'sinkPinName', 'edgeType', 'delayValue']

    filtered_graph = get_filtered_rdf_graph(properties, graph)
    filtered_graph.serialize(destination="fil_graph.ttl", format='turtle')
    print("Constructing DGL graph")
    data_dir = f"{ROOT_DIR}/data/"
    construct_dgl_main(filtered_graph, data_dir)

    print("Preprocessing DGL graph")
    gs = {}
    gs['gcd'] = dgl.load_graphs(f'{data_dir}/graph.dgl')[0]

    data_train, data_test = generate_ml_data(gs)

    with open(f'{data_dir}/data_train.pk', 'wb') as pkf:
        pk.dump(data_train, pkf)
    with open(f'{data_dir}/data_test.pk', 'wb') as pkf:
        pk.dump(data_test, pkf)
    
    print(f"The train data is dumped at {data_dir}/data_train.pk")
    
