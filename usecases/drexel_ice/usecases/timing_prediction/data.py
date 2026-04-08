import torch
from typing import List
from torch_geometric.data import Data
from torch_geometric.utils import from_networkx

def match_and_label_graphs(
    source_graphs: List,
    target_graphs: List,
    label_key: str = "arrival_time"
) -> List[Data]:
    """
    Match source and target timing path graphs by keys and attach target labels.

    This function:
        1. Matches source and target NetworkX graphs using a composite key:
           (netlist_id, startpoint, endpoint).
        2. Retrieves a graph-level label from the target graph (`label_key`).
        3. Extracts numeric node and graph-level features from the source graph.
        4. Converts the source NetworkX graph to a PyTorch Geometric Data object.
        5. Adds the label (`y`) and graph-level metadata features (`graph_x`).

    Args:
        source_graphs (List): Source NetworkX graphs (e.g., from placement stage).
        target_graphs (List): Target NetworkX graphs (e.g., from routing stage).
        label_key (str): Graph-level attribute in target graphs to use as regression label.

    Returns:
        List[Data]: PyTorch Geometric Data objects with:
            - x: Node feature matrix
            - edge_index: Graph connectivity
            - graph_x: Graph-level feature vector
            - y: Regression label tensor
    """
    # Build lookup for target graphs
    lookup = {
        (g.graph.get("netlist_id"), g.graph.get("startpoint"), g.graph.get("endpoint")): g
        for g in target_graphs
    }

    dataset = []

    for g in source_graphs:
        key = (g.graph.get("netlist_id"), g.graph.get("startpoint"), g.graph.get("endpoint"))
        if key not in lookup:
            continue

        target_graph = lookup[key]
        if label_key not in target_graph.graph:
            continue

        try:
            label = float(target_graph.graph[label_key])
        except (ValueError, TypeError):
            continue

        # Node-level numeric features
        feature_keys = sorted({
            k for _, d in g.nodes(data=True) for k, v in d.items()
            if isinstance(v, (int, float))
        })
        node_features = [
            [float(d.get(k, 0.0)) for k in feature_keys]
            for _, d in g.nodes(data=True)
        ]

        # Graph-level numeric features
        graph_keys = sorted(k for k, v in g.graph.items() if isinstance(v, (int, float)))
        graph_features = [float(g.graph.get(k, 0.0)) for k in graph_keys]

        # Convert to PyTorch Geometric Data
        data = from_networkx(g)
        data.x = torch.tensor(node_features, dtype=torch.float)
        data.graph_x = torch.tensor(graph_features, dtype=torch.float)
        data.y = torch.tensor([label], dtype=torch.float)

        dataset.append(data)

    return dataset
