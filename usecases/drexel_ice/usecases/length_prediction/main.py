import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from model import NetLengthPredictor
from data import load_placement_routing_data, prepare_dataloaders
from train_eval import train, evaluate
from utils import fix_seed

def run():
    """
    Main pipeline:
        1. Load data from ontology.
        2. Prepare DataLoaders.
        3. Initialize and train the model.
        4. Evaluate on the test set.
    """
    fix_seed(42)
    X, y = load_placement_routing_data()
    train_loader, X_test, y_test = prepare_dataloaders(X, y)

    model = NetLengthPredictor()
    train(model, train_loader)
    evaluate(model, X_test, y_test)


if __name__ == "__main__":
    run()
