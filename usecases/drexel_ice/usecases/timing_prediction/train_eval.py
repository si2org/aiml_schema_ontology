import pandas as pd
import torch
from torch import nn
from torch_geometric.loader import DataLoader
from typing import Tuple
from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent


# === Training / Evaluation ===

def run_training(
    label_key: str,
    model: nn.Module,
    train_loader: DataLoader,
    test_loader: DataLoader,
    is_wide: bool = False,
    epochs: int = 20
) -> Tuple[float, float]:
    """
    Train a GNN model and evaluate it on the test set.

    Args:
        label_key (str): Name of label being predicted.
        model (nn.Module): GNN model.
        train_loader (DataLoader): Training data.
        test_loader (DataLoader): Test data.
        is_wide (bool): Whether model expects graph-level features.
        epochs (int): Number of epochs.

    Returns:
        (float, float): MAE, MAPE from evaluation.
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_fn = nn.MSELoss()

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0

        for batch in train_loader:
            optimizer.zero_grad()

            if is_wide:
                graph_x = torch.stack([g.graph_x for g in batch.to_data_list()]).to(batch.x.device)
                pred = model(batch.x, batch.edge_index, batch.batch, graph_x)
            else:
                pred = model(batch.x, batch.edge_index, batch.batch)

            loss = loss_fn(pred.squeeze(), batch.y)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        print(f"Epoch {epoch:02d} | Loss: {avg_loss:.4f}")

    return evaluate_model(label_key, model, test_loader, is_wide)


def evaluate_model(
    label_key: str,
    model: nn.Module,
    loader: DataLoader,
    is_wide: bool = False
) -> Tuple[float, float]:
    """
    Evaluate a trained GNN model.

    Args:
        label_key (str): Name of label being predicted.
        model (nn.Module): Trained model.
        loader (DataLoader): Dataset to evaluate.
        is_wide (bool): Whether model expects graph-level features.

    Returns:
        (float, float): MAE, MAPE.
    """
    model.eval()
    preds, targets = [], []

    with torch.no_grad():
        for batch in loader:
            if is_wide:
                graph_x = torch.stack([g.graph_x for g in batch.to_data_list()]).to(batch.x.device)
                pred = model(batch.x, batch.edge_index, batch.batch, graph_x)
            else:
                pred = model(batch.x, batch.edge_index, batch.batch)

            preds.append(pred.squeeze())
            targets.append(batch.y)

    preds = torch.cat(preds)
    targets = torch.cat(targets)

    mae = torch.mean(torch.abs(preds - targets)).item()
    mape = torch.mean(torch.abs((preds - targets) / (targets + 1e-8))).item() * 100

    print(f"Test MAE: {mae:.4f} | MAPE: {mape:.2f}%")

    df = pd.DataFrame({
        "pred": preds.numpy().tolist(),
        "target": targets.numpy().tolist()
    })
    output_path = SCRIPT_DIR / "results" / f"{label_key}.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    return mae, mape
