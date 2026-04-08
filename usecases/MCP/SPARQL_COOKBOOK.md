# SPARQL Query Cookbook for EDA Ontology

This cookbook provides practical SPARQL query examples for exploring and using the EDA ontology. All queries use standard prefixes:

```sparql
PREFIX eda: <http://example.org/eda#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
```

---

## Basic Exploration

### List All Classes
```sparql
SELECT DISTINCT ?class ?label WHERE {
    ?class a owl:Class .
    OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?class
```

### Count Classes by Domain Pattern
```sparql
SELECT ?domain (COUNT(?class) as ?count) WHERE {
    ?class a owl:Class .
    BIND(
        IF(CONTAINS(STR(?class), "Timing"), "Timing",
        IF(CONTAINS(STR(?class), "Power"), "Power",
        IF(CONTAINS(STR(?class), "Physical"), "Physical",
        IF(CONTAINS(STR(?class), "Verif"), "Verification",
        "Other")))) as ?domain
    )
}
GROUP BY ?domain
ORDER BY DESC(?count)
```

### Get Class with Its Documentation
```sparql
SELECT ?class ?label ?comment WHERE {
    ?class a owl:Class .
    OPTIONAL { ?class rdfs:label ?label }
    OPTIONAL { ?class rdfs:comment ?comment }
    FILTER(BOUND(?comment))
}
```

---

## Class Hierarchy

### Get Direct Subclasses of a Class
```sparql
SELECT ?subclass ?label WHERE {
    ?subclass rdfs:subClassOf eda:EDAProcess .
    OPTIONAL { ?subclass rdfs:label ?label }
}
ORDER BY ?subclass
```

### Get Full Class Ancestry (Parents)
```sparql
SELECT ?class ?parent WHERE {
    eda:Placement rdfs:subClassOf+ ?parent .
    FILTER(isURI(?parent))
}
```

### Get Complete Hierarchy Tree
```sparql
SELECT ?class ?parent ?depth WHERE {
    {
        SELECT ?class ?parent (COUNT(?mid) as ?depth) WHERE {
            ?class rdfs:subClassOf* ?mid .
            ?mid rdfs:subClassOf* ?parent .
            FILTER(?class != ?parent)
            FILTER(isURI(?parent))
        }
        GROUP BY ?class ?parent
    }
}
ORDER BY ?depth ?parent ?class
```

### Find Root Classes (No Parent)
```sparql
SELECT ?class WHERE {
    ?class a owl:Class .
    FILTER NOT EXISTS {
        ?class rdfs:subClassOf ?parent .
        FILTER(isURI(?parent))
    }
    FILTER(STRSTARTS(STR(?class), "http://example.org/eda#"))
}
```

---

## Properties

### List All Object Properties with Domain/Range
```sparql
SELECT ?prop ?domain ?range WHERE {
    ?prop a owl:ObjectProperty .
    OPTIONAL { ?prop rdfs:domain ?domain }
    OPTIONAL { ?prop rdfs:range ?range }
}
ORDER BY ?prop
```

### List All Datatype Properties
```sparql
SELECT ?prop ?domain ?range WHERE {
    ?prop a owl:DatatypeProperty .
    OPTIONAL { ?prop rdfs:domain ?domain }
    OPTIONAL { ?prop rdfs:range ?range }
}
ORDER BY ?prop
```

### Find Properties Applicable to a Class
```sparql
SELECT ?prop ?range WHERE {
    ?prop rdfs:domain eda:TimingPath .
    OPTIONAL { ?prop rdfs:range ?range }
}
```

### Find Inverse Properties
```sparql
SELECT ?prop ?inverse WHERE {
    ?prop owl:inverseOf ?inverse .
}
```

---

## Disjointness and Constraints

### List All Disjoint Class Pairs
```sparql
SELECT ?class1 ?class2 WHERE {
    ?class1 owl:disjointWith ?class2 .
}
ORDER BY ?class1
```

### Check if Two Classes are Disjoint
```sparql
ASK {
    { eda:Placement owl:disjointWith eda:Routing }
    UNION
    { eda:Routing owl:disjointWith eda:Placement }
}
```

### Find Classes Disjoint with a Given Class
```sparql
SELECT ?disjoint WHERE {
    { eda:Placement owl:disjointWith ?disjoint }
    UNION
    { ?disjoint owl:disjointWith eda:Placement }
}
```

### Find All Restrictions on a Class
```sparql
SELECT ?class ?prop ?restriction WHERE {
    ?class rdfs:subClassOf ?restriction .
    ?restriction a owl:Restriction .
    ?restriction owl:onProperty ?prop .
}
```

---

## Domain-Specific Queries

### Timing Domain

**Get All Timing-Related Classes:**
```sparql
SELECT ?class ?label WHERE {
    ?class a owl:Class .
    FILTER(
        CONTAINS(STR(?class), "Timing") ||
        CONTAINS(STR(?class), "Clock") ||
        CONTAINS(STR(?class), "Delay") ||
        CONTAINS(STR(?class), "Slack") ||
        CONTAINS(STR(?class), "Path") ||
        CONTAINS(STR(?class), "SDC")
    )
    OPTIONAL { ?class rdfs:label ?label }
}
```

**Get Clock-Related Hierarchy:**
```sparql
SELECT ?class ?parent WHERE {
    ?class a owl:Class .
    ?class rdfs:subClassOf ?parent .
    FILTER(CONTAINS(STR(?class), "Clock"))
    FILTER(isURI(?parent))
}
```

### Physical Design Domain

**Get Physical Design Process Classes:**
```sparql
SELECT ?class WHERE {
    ?class rdfs:subClassOf+ eda:PhysicalDesign .
}
```

**Get Layout-Related Classes:**
```sparql
SELECT ?class WHERE {
    ?class a owl:Class .
    FILTER(
        CONTAINS(STR(?class), "Placement") ||
        CONTAINS(STR(?class), "Routing") ||
        CONTAINS(STR(?class), "CTS") ||
        CONTAINS(STR(?class), "Floorplan")
    )
}
```

### Power Domain

**Get Power Analysis Classes:**
```sparql
SELECT ?class WHERE {
    ?class a owl:Class .
    FILTER(
        CONTAINS(STR(?class), "Power") ||
        CONTAINS(STR(?class), "Voltage") ||
        CONTAINS(STR(?class), "UPF")
    )
}
```

### Verification Domain

**Get Verification Process Types:**
```sparql
SELECT ?class WHERE {
    ?class rdfs:subClassOf eda:Verification .
}
```

**Get DRC-Related Classes:**
```sparql
SELECT ?class WHERE {
    ?class a owl:Class .
    FILTER(
        CONTAINS(STR(?class), "DRC") ||
        CONTAINS(STR(?class), "LVS") ||
        CONTAINS(STR(?class), "Violation")
    )
}
```

---

## File Formats and Tools

### Get All File Format Classes
```sparql
SELECT ?format ?label WHERE {
    ?format a owl:Class .
    FILTER(CONTAINS(STR(?format), "File"))
    OPTIONAL { ?format rdfs:label ?label }
}
```

### Get Tool Classes
```sparql
SELECT ?tool ?label WHERE {
    ?tool rdfs:subClassOf* eda:Tool .
    ?tool a owl:Class .
    OPTIONAL { ?tool rdfs:label ?label }
}
```

### Find What a Tool Generates
```sparql
SELECT ?tool ?artifact WHERE {
    ?tool eda:generates ?artifact .
}
```

---

## Design Structure

### Get Design Components
```sparql
SELECT ?class WHERE {
    ?class a owl:Class .
    FILTER(
        ?class = eda:Design ||
        ?class = eda:Instance ||
        ?class = eda:Net ||
        ?class = eda:Pin ||
        ?class = eda:Port
    )
}
```

### Get Instance Hierarchy Classes
```sparql
SELECT ?class WHERE {
    ?class rdfs:subClassOf* eda:Instance .
    ?class a owl:Class .
}
```

---

## Statistics

### Count Triples by Predicate
```sparql
SELECT ?predicate (COUNT(*) as ?count) WHERE {
    ?s ?predicate ?o .
}
GROUP BY ?predicate
ORDER BY DESC(?count)
LIMIT 20
```

### Count Classes by Hierarchy Level
```sparql
SELECT ?depth (COUNT(?class) as ?count) WHERE {
    {
        SELECT ?class (COUNT(?parent) as ?depth) WHERE {
            ?class a owl:Class .
            ?class rdfs:subClassOf* ?parent .
            FILTER(isURI(?parent))
        }
        GROUP BY ?class
    }
}
GROUP BY ?depth
ORDER BY ?depth
```

### Get Most Connected Classes
```sparql
SELECT ?class (COUNT(?related) as ?connections) WHERE {
    ?class a owl:Class .
    {
        ?class rdfs:subClassOf ?related .
    } UNION {
        ?related rdfs:subClassOf ?class .
    } UNION {
        ?class owl:disjointWith ?related .
    } UNION {
        ?prop rdfs:domain ?class .
        BIND(?prop as ?related)
    }
}
GROUP BY ?class
ORDER BY DESC(?connections)
LIMIT 20
```

---

## Advanced Queries

### Find Classes Without Labels
```sparql
SELECT ?class WHERE {
    ?class a owl:Class .
    FILTER NOT EXISTS { ?class rdfs:label ?label }
    FILTER(STRSTARTS(STR(?class), "http://example.org/eda#"))
}
```

### Find Properties Without Domain
```sparql
SELECT ?prop WHERE {
    { ?prop a owl:ObjectProperty }
    UNION
    { ?prop a owl:DatatypeProperty }
    FILTER NOT EXISTS { ?prop rdfs:domain ?domain }
}
```

### Find Isolated Classes (No Relationships)
```sparql
SELECT ?class WHERE {
    ?class a owl:Class .
    FILTER NOT EXISTS { ?class rdfs:subClassOf ?parent . FILTER(isURI(?parent)) }
    FILTER NOT EXISTS { ?child rdfs:subClassOf ?class }
    FILTER NOT EXISTS { ?class owl:disjointWith ?other }
    FILTER NOT EXISTS { ?prop rdfs:domain ?class }
    FILTER(STRSTARTS(STR(?class), "http://example.org/eda#"))
}
```

### CONSTRUCT a Subgraph
```sparql
CONSTRUCT {
    ?class a owl:Class .
    ?class rdfs:subClassOf ?parent .
    ?class rdfs:label ?label .
}
WHERE {
    ?class rdfs:subClassOf* eda:PhysicalDesign .
    ?class a owl:Class .
    OPTIONAL { ?class rdfs:subClassOf ?parent . FILTER(isURI(?parent)) }
    OPTIONAL { ?class rdfs:label ?label }
}
```

---

## Using with Python

```python
from mcp_client import MCPOntologyClient

client = MCPOntologyClient("onto")
client.initialize("eda-ontology.ttl")

# Execute a query
result = client.query("""
    PREFIX eda: <http://example.org/eda#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT ?class WHERE {
        ?class rdfs:subClassOf eda:PhysicalDesign .
    }
""")

for row in result.data:
    print(row['class'])
```

---

## Tips

1. **Performance**: Use `LIMIT` for exploratory queries on large ontologies
2. **Filtering**: `FILTER(isURI(?x))` excludes blank nodes from results
3. **Optional**: Use `OPTIONAL` to include results even when values are missing
4. **Namespace**: The EDA ontology uses `http://example.org/eda#` namespace
5. **Case Sensitivity**: SPARQL string matching is case-sensitive by default; use `CONTAINS(LCASE(STR(?x)), "pattern")` for case-insensitive
