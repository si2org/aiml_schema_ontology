import torch.nn as nn
import torch.nn.functional as F


class NetLengthPredictor(nn.Module):
    """
    A simple feedforward neural network for predicting net lengths in VLSI designs.

    Architecture:
        - Input: 2 features (estimatedHpwl, numFanout)
        - Hidden Layer 1: 32 units, ReLU activation
        - Hidden Layer 2: 16 units, ReLU activation
        - Output: 1 unit (predicted net length)

    Methods:
        forward(x): Perform forward pass through the network.
    """

    def __init__(self):
        """Initialize network layers."""
        super().__init__()
        self.fc1 = nn.Linear(2, 32)
        self.fc2 = nn.Linear(32, 16)
        self.fc3 = nn.Linear(16, 1)

    def forward(self, x):
        """
        Forward pass through the network.

        Args:
            x (torch.Tensor): Input tensor of shape (batch_size, 2).

        Returns:
            torch.Tensor: Predicted net length of shape (batch_size, 1).
        """
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)
