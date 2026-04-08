from rdflib import Graph, RDF, RDFS, OWL, BNode
from rdflib.collection import Collection
from graphviz import Digraph

def get_class_label(graph, cls):
    """Generate a label for a class with its datatype properties."""
    label = cls.split("#")[-1]
    for prop in graph.subjects(RDF.type, OWL.DatatypeProperty):
        if (prop, RDFS.domain, cls) in graph:
            range_ = graph.value(prop, RDFS.range)
            if range_:
                prop_label = prop.split("#")[-1]
                datatype = range_.split("#")[-1] if "#" in range_ else range_.split("/")[-1]
                label += f"\n {prop_label} : {datatype}"
    return label

def add_class_nodes(graph, dot):
    """Add class nodes with datatype properties."""
    for cls in graph.subjects(RDF.type, OWL.Class):
        if not str(cls).startswith("http"):
            continue
        label = get_class_label(graph, cls)
        if cls.split("#")[-1] in ["Flow", "Stage", "Netlist", "ClockTree", "Net", "Wire", "Port", "Pin", "Instance", "StandardCell", "TimingPath", "TimingPathPin", "AreaMetrics", "PowerMetrics", "TimingMetrics", "CellMetrics"]:
            dot.node(cls.split("#")[-1], label=label, shape="box", style="filled", fillcolor="lightyellow")
        else:
            dot.node(cls.split("#")[-1], label=label, shape="box", style="filled", fillcolor="lightblue")

def add_subclass_edges(graph, dot):
    """Add subclass relationships."""
    for s, _, o in graph.triples((None, RDFS.subClassOf, None)):
        if str(s).startswith("http") and str(o).startswith("http"):
            dot.edge(o.split("#")[-1], s.split("#")[-1], label="subClassOf")

def extract_union_classes(graph, bnode):
    """Extract class names from an owl:unionOf BNode."""
    union = graph.value(bnode, OWL.unionOf)
    return [c.split("#")[-1] for c in Collection(graph, union)] if union else []

def add_object_properties(graph, dot):
    """Add object property edges with domain and range."""
    for prop in graph.subjects(RDF.type, OWL.ObjectProperty):
        domain = graph.value(prop, RDFS.domain)
        range_ = graph.value(prop, RDFS.range)

        if not range_:
            continue

        domain_classes = []
        if isinstance(domain, BNode) and (domain, OWL.unionOf, None) in graph:
            domain_classes = extract_union_classes(graph, domain)
        elif domain:
            domain_classes = [domain.split("#")[-1]]

        for cls in domain_classes:
            # dot.edge(cls, range_.split("#")[-1], label=prop.split("#")[-1])
            dot.edge(cls, range_.split("#")[-1])

def build_ontology_diagram(ttl_path, output_name):
    """Build and render the ontology diagram."""
    g = Graph()
    g.parse(ttl_path, format="turtle")
    dot = Digraph(comment="Ontology Class Diagram")

    add_class_nodes(g, dot)
    add_subclass_edges(g, dot)
    add_object_properties(g, dot)

    dot.render(output_name, format="png", cleanup=False)
    print(f"Graph generated: {output_name}.png")

# Run the diagram generator
build_ontology_diagram("ontology/eda-ontology.ttl", "ontology/eda-ontology")
build_ontology_diagram("ontology/eda-schema.ttl", "ontology/eda-schema")
