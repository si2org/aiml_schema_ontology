# SPDX-FileCopyrightText: Copyright (c) 2022 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import pandas as pd
import numpy as np
from numpy.random import *
import time
import sys, os, argparse
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn import preprocessing
import matplotlib.pyplot as plt

sys.path.append("../../src/")
from datagen_ttl import *

np.random.seed(42)


def generate_ML_data(pin_graph_dataset):
    #Gathering dataset for training and testing
    if 'edgeType' not in pin_graph_dataset.columns:
        print("Error: 'edgeType' column missing; unable to isolate net arcs. Using entire dataset.\n")
        net_pin_arcs_df = pin_graph_dataset.copy()
    else:
        net_pin_arcs_df = pin_graph_dataset[pin_graph_dataset['edgeType'] == 1].copy()

    net_pin_arcs_df["sourceNode_cell_type"] = net_pin_arcs_df["sourceNode_libcellName"].str.split('_').str[0]
    net_pin_arcs_df["sinkNode_cell_type"] = net_pin_arcs_df["sinkNode_libcellName"].str.split('_').str[0]
    letter_to_int = {letter: idx for idx, letter in enumerate(sorted(net_pin_arcs_df['sourceNode_cell_type'].unique()))}
    net_pin_arcs_df['sourceNode_cell_id'] = net_pin_arcs_df['sourceNode_cell_type'].map(letter_to_int)
    net_pin_arcs_df['sinkNode_cell_id'] = net_pin_arcs_df['sinkNode_cell_type'].map(letter_to_int)
    
    net_pin_arcs_df['dist_x'] = (net_pin_arcs_df['sinkNode_pinX'] - net_pin_arcs_df['sourceNode_pinX']).abs()
    net_pin_arcs_df['dist_y'] = (net_pin_arcs_df['sinkNode_pinY'] - net_pin_arcs_df['sourceNode_pinY']).abs()

    net_pin_arcs_df = net_pin_arcs_df.dropna()

    # x, y: distance between driver and the target sink
    # cap, cap_sum: sink capacitance
    # driver and sink libcell 
    
    requested_features = [
        "dist_x",
        "dist_y",
        "sinkNode_inputCapacitance",
        "sourceNode_loadCapacitance",
        "sourceNode_cell_id",
        "sinkNode_cell_id",
        "sinkNode_netCapacitance",
        "sinkNode_netLength",
    ]
    available_features = [feat for feat in requested_features if feat in net_pin_arcs_df.columns]
    missing_features = [feat for feat in requested_features if feat not in available_features]
    if missing_features:
        print(f"Error: Missing columns {missing_features} in dataset. Continuing without them.\n")
    if not available_features:
        raise ValueError("No feature columns available after checking dataset. Cannot proceed.")

    features_df = net_pin_arcs_df.loc[:, available_features]
    features_csv_path = Path("preroute_delay_predictor_features.csv")
    print(f"Final features dataset saved to {features_csv_path}.")
    features_df.to_csv(features_csv_path, index=False)

    features = features_df.to_numpy().astype(float)

    if "delayValue" not in net_pin_arcs_df.columns:
        raise ValueError("Required label column 'delayValue' missing from dataset. Cannot proceed.")
    labels = net_pin_arcs_df.loc[:, ["delayValue"]].to_numpy().astype(float)
    
    features = preprocessing.normalize(features, axis=0)
    labels = preprocessing.normalize(labels, axis=0)
    labels = labels.reshape([-1,])
    
    train_x, test_x, train_y, test_y = train_test_split(features, labels, test_size=0.05, random_state=42)
    
    return train_x, test_x, train_y, test_y


def train_model(train_x, train_y):
    nb_train_samples = train_x.shape[0]
    nb_test_samples = train_y.shape[0]
    
    print("Training Machine Learning Model")
    
    nb_estim = 500
    max_feat = 0.5
    model = RandomForestRegressor(n_estimators=nb_estim, max_features=max_feat, random_state=42)
    model.fit(train_x, train_y)
    return model


def evaluate_model(model, train_x, train_y, test_x, test_y):
    pred = model.predict(train_x)
    
    plt.figure()
    plt.scatter(pred, train_y, label = "Training")

    pred = model.predict(test_x)
    plt.scatter(pred, test_y, label = "Testing")
    
    data_range = np.arange(min(np.min(train_y), np.min(test_y)), 
                           max(np.max(train_y), np.max(test_y)),
                           0.005
                          )
    plt.plot(data_range, data_range, label="Reference")
    
    plt.title("Accuracy on training data and testing data")
    
    plt.legend()
    plt.xlabel("Reference")
    plt.ylabel("Predicted")
    plt.savefig("preroute_delay_prediction_plot.png")
    plt.close()
    print("Saved evaluation plot to preroute_delay_prediction_plot.png.")


if __name__ == "__main__":

    # Set Schema path
    repo_root = Path(__file__).resolve().parents[5]
    schema_directory = repo_root / "ontology"
    croissant_directory = Path(__file__).resolve().parents[2] / "croissant"
    ontology_files = [
        schema_directory / "eda_ontology.ttl",
        schema_directory / "eda-ontology-adapter.ttl",
    ]
    metadata_file = croissant_directory / "circuitops_croissant_metadata_ontology.json"

    # Load Ontology and Metadata
    graph = load_ontologies(ontology_files)
    metadata = load_metadata(str(metadata_file))
    
    # Pre-route net delay predictor
    driver_features = ["pinName", "libcellName", "loadCapacitance", "setupRiseArrival", "setupFallArrival", "pinX", "pinY"]
    sink_features = ["pinName", "libcellName", "inputCapacitance", "setupRiseArrival", "setupFallArrival", "pinX", "pinY", "netCapacitance", "netLength"]

    graph_features = {
        "sourceNode": driver_features,
        "sinkNode": sink_features
    }
 
    # Dataset Generation
    timing_graph_uri = EDA.TimingGraph 
    pin_graph_dataset = get_graph(graph, timing_graph_uri, graph_features, metadata, metadata_file)

    #print(pin_graph_dataset.columns)

    X_train, X_test, Y_train, Y_test = generate_ML_data(pin_graph_dataset)

    model = train_model(X_train, Y_train)
