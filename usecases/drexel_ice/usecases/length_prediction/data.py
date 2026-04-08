import torch
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from ontology.eda_schema_ontology import EDA, get_ontology_df

def load_placement_routing_data():
    """
    Load and merge placement-phase features with routing-phase targets for nets.

    This function:
        1. Loads 'estimatedHpwl' and 'numFanout' for each net from the placement phase.
        2. Loads 'netLength' for each net from the routing phase.
        3. Merges datasets on 'name' and removes incomplete rows.

    Returns:
        tuple:
            - X (ndarray): Feature matrix of shape (n_samples, 2).
            - y (ndarray): Target vector of shape (n_samples,).
    """
    place_df = get_ontology_df(
        entity=EDA.Net,
        phase="detailed_place",
        properties=["name", "estimatedHpwl", "numFanout"],
    )

    route_df = get_ontology_df(
        entity=EDA.Net,
        phase="detailed_route",
        properties=["name", "netLength"],
    )

    df = place_df.merge(route_df, on="name", how="inner")
    df = df.dropna(subset=["estimatedHpwl", "numFanout", "netLength"])

    X = df[["estimatedHpwl", "numFanout"]].astype(float).values
    y = df["netLength"].astype(float).values

    return X, y


def prepare_dataloaders(X, y, batch_size=32):
    """
    Standardize features, split into train/test sets, and create PyTorch DataLoaders.

    Args:
        X (ndarray): Feature matrix.
        y (ndarray): Target vector.
        batch_size (int, optional): Batch size for DataLoader. Defaults to 32.

    Returns:
        tuple:
            - train_loader (DataLoader): Training data loader.
            - X_test (torch.Tensor): Standardized test features.
            - y_test (torch.Tensor): Test targets.
    """
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    X_train = torch.tensor(X_train, dtype=torch.float32)
    y_train = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
    X_test = torch.tensor(X_test, dtype=torch.float32)
    y_test = torch.tensor(y_test, dtype=torch.float32).unsqueeze(1)

    train_loader = DataLoader(
        TensorDataset(X_train, y_train), batch_size=batch_size, shuffle=True
    )

    return train_loader, X_test, y_test
