import re
from pathlib import Path
import pandas as pd
import networkx as nx
from rdflib import Graph, RDF, RDFS, OWL, Namespace, BNode
from rdflib.collection import Collection
from mlcroissant import Dataset
from graphviz import Digraph

# === Configuration ===
ONTOLOGY_DIR = Path(__file__).resolve().parent
CROISSANT_PATH = ONTOLOGY_DIR.parent / "combined_croissant_metadata.json"
ONTOLOGY_ROOT = ONTOLOGY_DIR.parent.parent.parent / "ontology"
TTL_PATHS = [
    ONTOLOGY_ROOT / "eda-ontology-adapter.ttl",
    ONTOLOGY_ROOT / "eda_ontology.ttl",
]

EDA = Namespace("http://example.org/eda#")

# === Ontology Utilities ===

def load_ontology(ttl_paths: str) -> Graph:
    """
    Load an RDF ontology from a Turtle (.ttl) file.

    This function reads a Turtle file, parses it into an RDFLib Graph object,
    and binds the EDA namespace for easier querying.

    Args:
        ttl_paths (str): Path to the .ttl ontology file.

    Returns:
        Graph: RDFLib Graph containing the parsed ontology.
    """
    g = Graph()
    for ttl_path in ttl_paths:
        g.parse(ONTOLOGY_DIR / ttl_path, format="turtle")
    g.bind("eda", EDA)
    return g


def strip_ns(uri: str) -> str:
    """
    Extract the local name from a URI by stripping its namespace.

    Args:
        uri (str): Full URI string.

    Returns:
        str: Local name without namespace.
    """
    return uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]


def get_class_properties(g: Graph, class_uri, prop_type) -> list[str]:
    """
    Retrieve property names (datatype or object) for a specific RDF class.

    Args:
        g (Graph): RDFLib Graph containing the ontology.
        class_uri (URIRef): RDF class URI.
        prop_type (URIRef): OWL.DatatypeProperty or OWL.ObjectProperty.

    Returns:
        list[str]: List of property names without namespaces.
    """
    return [
        strip_ns(p)
        for p in g.subjects(RDF.type, prop_type)
        if (p, RDFS.domain, class_uri) in g
    ]


def get_class_label(g: Graph, cls) -> str:
    """
    Create a display label for a class including its datatype properties and types.

    Args:
        g (Graph): RDFLib Graph containing the ontology.
        cls (URIRef): RDF class URI.

    Returns:
        str: Multi-line string label with class name and properties.
    """
    label = strip_ns(cls)
    for p in g.subjects(RDF.type, OWL.DatatypeProperty):
        if (p, RDFS.domain, cls) in g:
            range_ = g.value(p, RDFS.range)
            if range_:
                label += f"\n {strip_ns(p)} : {strip_ns(range_)}"
    return label


def extract_union_classes(g: Graph, bnode: BNode) -> list[str]:
    """
    Extract class names from an OWL unionOf blank node.

    Args:
        g (Graph): RDFLib Graph containing the ontology.
        bnode (BNode): Blank node with OWL.unionOf.

    Returns:
        list[str]: Class names without namespaces.
    """
    union = g.value(bnode, OWL.unionOf)
    return [strip_ns(c) for c in Collection(g, union)] if union else []


def add_class_nodes(g: Graph, dot: Digraph):
    """
    Add OWL class nodes to a Graphviz diagram.

    Highlights certain important classes in yellow.

    Args:
        g (Graph): RDFLib Graph containing the ontology.
        dot (Digraph): Graphviz Digraph to add nodes to.
    """
    highlights = {
        "Flow", "Stage", "Netlist", "ClockTree", "Net", "Wire", "Port", "Pin", "Instance",
        "StandardCell", "TimingPath", "TimingPathPin", "AreaMetrics", "PowerMetrics",
        "TimingMetrics", "CellMetrics"
    }
    for cls in g.subjects(RDF.type, OWL.Class):
        if str(cls).startswith("http"):
            name = strip_ns(cls)
            dot.node(
                name,
                label=get_class_label(g, cls),
                shape="box",
                style="filled",
                fillcolor="lightyellow" if name in highlights else "lightblue"
            )


def add_subclass_edges(g: Graph, dot: Digraph):
    """
    Add rdfs:subClassOf edges between classes in the diagram.

    Args:
        g (Graph): RDFLib Graph containing the ontology.
        dot (Digraph): Graphviz Digraph to add edges to.
    """
    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        if str(s).startswith("http") and str(o).startswith("http"):
            dot.edge(strip_ns(o), strip_ns(s), label="subClassOf")


def add_object_properties(g: Graph, dot: Digraph):
    """
    Add edges for OWL object properties from domain to range classes.

    Args:
        g (Graph): RDFLib Graph containing the ontology.
        dot (Digraph): Graphviz Digraph to add edges to.
    """
    for p in g.subjects(RDF.type, OWL.ObjectProperty):
        domain, range_ = g.value(p, RDFS.domain), g.value(p, RDFS.range)
        if not range_:
            continue
        domains = extract_union_classes(g, domain) if isinstance(domain, BNode) else [strip_ns(domain)] if domain else []
        for d in domains:
            dot.edge(d, strip_ns(range_))


def build_ontology_diagram(ttl_path: str, output_name: str):
    """
    Build and render an ontology diagram as a PNG image.

    Args:
        ttl_path (str): Path to the ontology Turtle file.
        output_name (str): Output PNG filename (without extension).
    """
    g = load_ontology(ttl_path)
    dot = Digraph(comment="Ontology Diagram")
    add_class_nodes(g, dot)
    add_subclass_edges(g, dot)
    add_object_properties(g, dot)
    dot.render(output_name, format="png", cleanup=False)
    print(f"Ontology diagram saved to: {output_name}.png")

# === Croissant Utilities ===

def load_croissant_dataframe(dataset: Dataset, record_key: str) -> pd.DataFrame:
    """
    Load a Croissant record group into a pandas DataFrame.

    Decodes byte strings to UTF-8 and removes record key prefixes from column names.

    Args:
        dataset (Dataset): Croissant Dataset object.
        record_key (str): Key identifying the record group in the dataset.

    Returns:
        pd.DataFrame: Cleaned DataFrame.
    """
    df = pd.DataFrame(dataset.records(record_key))
    df.columns = df.columns.str.replace(f"{record_key}/", "", regex=False)
    # applymap was changed to map in Pandas version 2.1.0
    if hasattr(pd.DataFrame,"map"):
        return df.map(lambda x: x.decode() if isinstance(x, bytes) else x)
    else:
        return df.applymap(lambda x: x.decode() if isinstance(x, bytes) else x)

# === Graph Builders ===

def build_graphs(df_graphs, df_edges, df_nodes, group_keys, graph_props, node_props, node_id_field):
    """
    Construct NetworkX DiGraphs from grouped edge and node datasets.

    Args:
        df_graphs (pd.DataFrame): Graph-level metadata.
        df_edges (pd.DataFrame): Edge list between nodes.
        df_nodes (pd.DataFrame): Node-level metadata.
        group_keys (list[str]): Columns identifying unique graphs.
        graph_props (list[str]): Properties to attach to the graph object.
        node_props (list[str]): Properties to attach to each node.
        node_id_field (str): Column name used as the node's identifier.

    Returns:
        list[nx.DiGraph]: List of constructed graphs.
    """
    df_graphs = df_graphs[[c for c in df_graphs.columns if c in graph_props + group_keys]]
    graphs = []
    for key, edges in df_edges.groupby(group_keys):
        G = nx.DiGraph()

        # Add edges
        for _, row in edges.iterrows():
            G.add_edge(row["source"], row["target"], **row.drop(["source", "target"]).to_dict())

        # Add graph-level attributes
        key_dict = dict(zip(group_keys, key)) if isinstance(key, tuple) else {group_keys[0]: key}
        matched_graph = df_graphs[df_graphs[group_keys].eq(pd.Series(key_dict)).all(axis=1)]
        if not matched_graph.empty:
            G.graph.update(matched_graph.iloc[0].to_dict())

        # Add nodes with attributes
        matched_nodes = df_nodes[df_nodes[group_keys].eq(pd.Series(key_dict)).all(axis=1)]
        for _, node in matched_nodes.iterrows():
            attrs = {k: node[k] for k in node.index if k in node_props and k not in group_keys}
            G.add_node(node[node_id_field], **attrs)

        graphs.append(G)
    return graphs


def tag_nodes(df, type_name):
    """
    Add 'node_id' and 'node_type' columns to a DataFrame.

    Args:
        df (pd.DataFrame): Original node DataFrame.
        type_name (str): Type label to assign.

    Returns:
        pd.DataFrame: Updated DataFrame with tagging.
    """
    df = df.copy()
    df["node_id"] = df["name"]
    df["node_type"] = type_name
    return df


def get_netlist_graphs(stage_name: str | None = None) -> list[nx.DiGraph]:
    """
    Build netlist-level graphs from Croissant metadata.

    Args:
        stage_name (str | None): Optional design phase filter.

    Returns:
        list[nx.DiGraph]: Netlist-level graphs.
    """
    g = load_ontology(TTL_PATHS)
    dataset = Dataset(CROISSANT_PATH)
    datatype_props = get_class_properties(g, EDA.Netlist, OWL.DatatypeProperty)

    df_graphs = load_croissant_dataframe(dataset, "netlist_records")
    df_edges = load_croissant_dataframe(dataset, "netlists_graph_records")
    df_nodes = pd.concat([
        tag_nodes(load_croissant_dataframe(dataset, key), t)
        for key, t in [
            ("gate_records", "Gate"),
            ("net_records", "Net"),
            ("port_records", "Port"),
            ("pin_records", "Pin")
        ]
    ], ignore_index=True)

    if stage_name:
        for df in [df_graphs, df_edges, df_nodes]:
            if "phase" in df.columns:
                df.drop(df[df["phase"] != stage_name].index, inplace=True)

    if not {"source", "target"} <= set(df_edges.columns):
        raise ValueError("Missing 'source' or 'target' in netlists_graph_records")

    df_edges.setdefault("sort_index", 0)
    return build_graphs(df_graphs, df_edges, df_nodes, ["netlist_id"], datatype_props, datatype_props, "node_id")


def get_timing_path_graphs(stage_name: str | None = None) -> list[nx.DiGraph]:
    """
    Build timing path graphs from Croissant metadata.

    Args:
        stage_name (str | None): Optional design phase filter.

    Returns:
        list[nx.DiGraph]: Timing path graphs.
    """
    g = load_ontology(TTL_PATHS)
    dataset = Dataset(CROISSANT_PATH)

    df_graphs = load_croissant_dataframe(dataset, "timing_path_records")
    graph_props = get_class_properties(g, EDA.TimingPath, OWL.DatatypeProperty)
    df_edges = load_croissant_dataframe(dataset, "timing_path_graph_records")
    df_nodes = load_croissant_dataframe(dataset, "timing_path_pin_records")
    node_props = get_class_properties(g, EDA.TimingPathPin, OWL.DatatypeProperty)

    if stage_name:
        for df in [df_graphs, df_edges, df_nodes]:
            df.drop(df[df["phase"] != stage_name].index, inplace=True)

    group_keys = ["netlist_id", "startpoint", "endpoint", "pathType"]
    return build_graphs(df_graphs, df_edges, df_nodes, group_keys, graph_props, node_props, "pin")

# === Ontology DataFrame Loader ===

def get_ontology_df(entity, phase="detailed_route", properties=None, validate=False) -> pd.DataFrame:
    """
    Load a Croissant record group for a given ontology entity.

    Args:
        entity (URIRef): OWL class URI.
        phase (str): Filter for design stage (default: 'detailed_route').
        properties (list[str] | None): List of properties to keep.
                                       If None, uses all datatype properties from ontology.
        validate (bool): If True, raise ValueError if any requested properties are missing.

    Returns:
        pd.DataFrame: Filtered DataFrame with selected properties.
    """
    g = load_ontology(TTL_PATHS)
    dataset = Dataset(CROISSANT_PATH)
    class_name = strip_ns(entity)
    record_key = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower() + "_records"

    df = load_croissant_dataframe(dataset, record_key)
    df = df[df["phase"] == phase]

    if properties is None:
        properties = get_class_properties(g, entity, OWL.DatatypeProperty)

    missing = [p for p in properties if p not in df.columns]
    if validate and missing:
        raise ValueError(f"Missing properties in dataset: {missing}")

    return df[[p for p in properties if p in df.columns]].copy()
