import pandas as pd
import numpy as np
from numpy.random import *
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn import preprocessing
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
from sklearn.metrics import mean_squared_error, max_error, mean_absolute_error
import sys
from pathlib import Path
sys.path.append("../../src/")

from datagen_ttl import *


def format_decimal(value: float, decimal_places: int = 12) -> str:
    """Format floats deterministically by limiting decimal places."""
    formatted = f"{value:.{decimal_places}f}"
    if "." in formatted:
        return formatted.rstrip("0").rstrip(".")
    return formatted

def generate_ML_data(pin_graph_dataset):
    # ML data extraction
    # Features: input tran, oad cap, cell type
    # Label: arc delay
    
    if 'edgeType' not in pin_graph_dataset.columns:
        print("Error: 'edgeType' column missing; unable to isolate cell arcs. Using entire dataset.\n")
        cell_pin_arcs_df = pin_graph_dataset.copy()
    else:
        cell_pin_arcs_df = pin_graph_dataset[pin_graph_dataset['edgeType'] == 0].copy()

    cell_pin_arcs_df["cell_type"] = cell_pin_arcs_df["sourceNode_libcellName"].str.split('_').str[0]
    letter_to_int = {letter: idx for idx, letter in enumerate(sorted(cell_pin_arcs_df['cell_type'].unique()))}
    cell_pin_arcs_df['cell_type_coded'] = cell_pin_arcs_df['cell_type'].map(letter_to_int)

    base_features = ['sourceNode_worstSlew', 'sinkNode_loadCapacitance', 'cell_type_coded']
    available_features = [feat for feat in base_features if feat in cell_pin_arcs_df.columns]
    missing_features = [feat for feat in base_features if feat not in available_features]
    if missing_features:
        print(f"Error: Missing columns {missing_features} in dataset. Continuing without them.")
    label_column = 'delayValue'
    if label_column not in cell_pin_arcs_df.columns:
        raise ValueError("Required label column 'delayValue' missing from dataset. Cannot proceed.")
    if not available_features:
        raise ValueError("No feature columns available after checking dataset. Cannot proceed.")

    selected_columns = available_features + [label_column]
    data = cell_pin_arcs_df.loc[:, selected_columns]

    print("Final dataset created for ML model training and is available as a dataframe and saved in CSV.")
    data.to_csv('arc_delay_predictor_dataframe.csv', index=False)
    #print(data)
    
    X = data.iloc[:, :-1]
    y = data.iloc[:, -1]
    
    # Splitting into train and test datasets
    X_train, X_test, y_train, Y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Normalizing the feature columns
    scaler = StandardScaler()
    print("Training the model using the dataset.")
    X_train_normalized = scaler.fit_transform(X_train)
    X_test_normalized = scaler.transform(X_test)
    
    return X_train_normalized, X_test_normalized, y_train, Y_test

def train_rf_model(X_train, Y_train):
    # Training the RF model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, Y_train)
    return model

def write_mlcard_info(test_acc):
    mlcard_info = {
     'model': 'RandomForestRegressor',
     'version': '1.0.0',
     'architecture': 'Ensemble of Decision Trees',
     'loss_function': None, 
     'optimizer': 'Randomized Search/Tree-based Growth',  
     'batch_size': None,  
     'learning_rate': None,  
     'epochs': None,  
     'dropout_rate': None,  
     'inference_latency': None,  
     'memory_footprint': None,  
     'training_accuracy': None,  
     'test_accuracy': test_acc  
    }

    # Convert the dictionary to a pandas DataFrame
    mlcard_df = pd.DataFrame([mlcard_info])

    # Write the DataFrame to a CSV file
    mlcard_df.to_csv('mlcard_properties.csv', index=False)
   
def evaluate_model(model, X_test, Y_test):
    # Making predictions
    Y_predict = model.predict(X_test)
    
    mse = mean_squared_error(Y_test, Y_predict)
    mae = mean_absolute_error(Y_test,Y_predict)
    rmse = np.sqrt(mse)
    max_err = max_error(Y_test, Y_predict)
    
    print(f"Mean Absolute Error (MAE):", mae)
    print(f"Mean Squared Error (MSE):", mse)
    print(f"Root Mean Squared Error (RMSE):", rmse)
    
    Y_predict = Y_predict.reshape(-1)
    errors = Y_predict - Y_test
    abs_errors = abs(errors)
    error_percentages = (abs_errors / Y_test) * 100
    mean_percent = sum(error_percentages) / len(error_percentages)
    write_mlcard_info(100-mean_percent)
    print("Max Error : ", max(abs_errors))
    print("Maximum Error %:", max(error_percentages))
    print("Mean Error %:", format_decimal(mean_percent))


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
    
    # Arc delay predictor
    driver_features = ["pinName", "worstSlew", "libcellName"]
    sink_features = ["pinName", "loadCapacitance"]

    graph_features = {
        "sourceNode": driver_features,
        "sinkNode": sink_features
    }

    #print("Features:", graph_features)
    #print('\n')

    # Dataset Generation
    timing_graph_uri = EDA.TimingGraph 
    pin_graph_dataset = get_graph(graph, timing_graph_uri, graph_features, metadata, metadata_file)
    
    #cell_pin_arcs_df = generate_dataset(IR_path)

    X_train, X_test, Y_train, Y_test = generate_ML_data(pin_graph_dataset)

    model = train_rf_model(X_train, Y_train)

    evaluate_model(model, X_test, Y_test)
