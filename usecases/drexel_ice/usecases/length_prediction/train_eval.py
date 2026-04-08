import torch
import torch.nn as nn
import pandas as pd
from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent

def train(model, loader, epochs=1000, lr=1e-3):
    """
    Train the neural network on the provided dataset.

    Args:
        model (nn.Module): PyTorch model to train.
        loader (DataLoader): DataLoader for training data.
        epochs (int, optional): Number of training epochs. Defaults to 1000.
        lr (float, optional): Learning rate for Adam optimizer. Defaults to 1e-3.
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    for epoch in range(epochs):
        model.train()
        total_loss = 0.0

        for xb, yb in loader:
            pred = model(xb)
            loss = loss_fn(pred, yb)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        print(f"Epoch {epoch + 1}/{epochs}, Loss: {total_loss:.4f}")


def evaluate(model, X_test, y_test):
    """
    Evaluate the trained model on the test dataset.

    Computes and prints:
        - Mean Absolute Error (MAE)
        - Maximum Absolute Error

    Args:
        model (nn.Module): Trained PyTorch model.
        X_test (torch.Tensor): Test feature data.
        y_test (torch.Tensor): Test target data.
    """
    model.eval()
    with torch.no_grad():
        preds = model(X_test).squeeze()
        targets = y_test.squeeze()

        abs_error = torch.abs(preds - targets)
        pct_error = abs_error / (targets + 1e-8) * 100

        print(f"\nMAE: {abs_error.mean():.4f}")
        print(f"Max Error: {abs_error.max():.4f}")

        df = pd.DataFrame({
            "pred": preds.numpy().tolist(),
            "target": targets.numpy().tolist()
        })
        output_path = SCRIPT_DIR / "results" / "results.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
