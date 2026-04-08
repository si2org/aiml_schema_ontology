import torch
import torch.nn.functional as F
from torch import nn
from torch_geometric.nn import GCNConv, global_mean_pool

# === GNN Models ===

class DeepGNN(nn.Module):
    """
    2-layer Graph Convolutional Network (GCN) for graph-level regression.

    Architecture:
        - GCNConv -> ReLU
        - GCNConv -> ReLU
        - Global mean pooling over nodes
        - Linear output layer

    Args:
        in_channels (int): Number of input node features.
        hidden (int, optional): Hidden layer size. Defaults to 64.
    """

    def __init__(self, in_channels: int, hidden: int = 64):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden)
        self.conv2 = GCNConv(hidden, hidden)
        self.out = nn.Linear(hidden, 1)

    def forward(self, x, edge_index, batch):
        """
        Forward pass.

        Args:
            x (Tensor): Node feature matrix.
            edge_index (Tensor): Graph connectivity.
            batch (Tensor): Batch assignment for each node.

        Returns:
            Tensor: Predicted graph-level output.
        """
        x = F.relu(self.conv1(x, edge_index))
        x = F.relu(self.conv2(x, edge_index))
        x = global_mean_pool(x, batch)
        return self.out(x)


class WideAndDeepGNN(nn.Module):
    """
    Graph neural network that fuses node-based GNN features (deep path)
    with graph-level metadata features (wide path).

    Architecture:
        - Node path: GCNConv -> ReLU -> GCNConv -> ReLU -> global mean pool
        - Graph path: Linear projection -> ReLU
        - Concatenate both paths -> Linear output layer

    Args:
        node_in (int): Number of input node features.
        graph_in (int): Number of input graph-level features.
        hidden (int, optional): Hidden layer size. Defaults to 64.
    """

    def __init__(self, node_in: int, graph_in: int, hidden: int = 64):
        super().__init__()
        self.conv1 = GCNConv(node_in, hidden)
        self.conv2 = GCNConv(hidden, hidden)
        self.graph_proj = nn.Linear(graph_in, hidden)
        self.out = nn.Linear(hidden * 2, 1)

    def forward(self, x, edge_index, batch, graph_x):
        """
        Forward pass.

        Args:
            x (Tensor): Node feature matrix.
            edge_index (Tensor): Graph connectivity.
            batch (Tensor): Batch assignment for each node.
            graph_x (Tensor): Graph-level feature matrix.

        Returns:
            Tensor: Predicted graph-level output.
        """
        x = F.relu(self.conv1(x, edge_index))
        x = F.relu(self.conv2(x, edge_index))
        x = global_mean_pool(x, batch)
        g = F.relu(self.graph_proj(graph_x))
        return self.out(torch.cat([x, g], dim=1))
