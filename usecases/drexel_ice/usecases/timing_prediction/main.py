import sys
import os
from sklearn.model_selection import train_test_split
from torch_geometric.loader import DataLoader

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ontology.eda_schema_ontology import get_timing_path_graphs
from data import match_and_label_graphs
from models import DeepGNN, WideAndDeepGNN
from train_eval import run_training
from utils import fix_seed

# === Main Driver ===

def run(label_key: str):
    """
    End-to-end pipeline for training and evaluating GNN models
    on timing path graphs for a given label.

    The pipeline:
        1. Loads placement and routing timing path graphs.
        2. Matches graphs and assigns labels from the target set.
        3. Splits into training and test sets.
        4. Trains a basic GNN (DeepGNN).
        5. Trains a wide+deep GNN (WideAndDeepGNN).

    Args:
        label_key (str): Name of the graph-level attribute to predict.
    """
    fix_seed(42)

    print(f"Starting experiment for label: '{label_key}'")
    placement_graphs = get_timing_path_graphs("detailed_place")
    routing_graphs = get_timing_path_graphs("detailed_route")

    dataset = match_and_label_graphs(placement_graphs, routing_graphs, label_key=label_key)
    if not dataset:
        raise ValueError(f"No matched graphs found for label: {label_key}")

    train_set, test_set = train_test_split(dataset, test_size=0.2, random_state=42)
    train_loader = DataLoader(train_set, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_set, batch_size=32)

    node_in = train_set[0].x.shape[1]
    graph_in = train_set[0].graph_x.shape[0]

    print(f"Training DeepGNN on '{label_key}'")
    gnn = DeepGNN(node_in)
    run_training(label_key, gnn, train_loader, test_loader, is_wide=False)

    print(f"Training WideAndDeepGNN on '{label_key}'")
    wide = WideAndDeepGNN(node_in, graph_in)
    run_training(label_key, wide, train_loader, test_loader, is_wide=True)


if __name__ == "__main__":
    run("arrivalTime")
    run("requiredTime")
    run("slack")
