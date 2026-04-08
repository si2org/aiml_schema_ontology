# Timing Prediction — Graph Neural Network for Timing Path Estimation

This module demonstrates how to use **graph-based representations of timing paths** from an Electronic Design Automation (EDA) flow to **predict timing characteristics** using Graph Neural Networks (GNNs).  

It builds on the `eda_schema_ontology.py` utilities to load placement and routing timing graphs, match them, and train models that leverage both **node-level** and **graph-level** features.

---

## 📌 Context in the AIML_Schema_Ontology Project

This is one of the machine learning use cases in the [`AIML_Schema_Ontology`](../../README.md) repository:

- **Goal** — Predict `arrival_time`, `required_time`, and `slack` *before* the routing phase.
- **Data Source** — Ontology-based timing graphs generated from detailed placement and detailed routing phases.
- **Benefit** — Enables early timing analysis, guiding optimization before expensive full routing and static timing analysis.

---

## 📂 Folder Structure

```
usecases/timing_prediction/
├── data.py         # Matching placement and routing graphs, building PyG datasets
├── models.py       # GNN model definitions (DeepGNN, WideAndDeepGNN)
├── train_eval.py   # Training and evaluation loops (MAE, MAPE)
└── main.py         # Pipeline entry point for running all label predictions
```

---

## 🔍 Features Used

The models use **two types of features**:

### Node-Level Features
Numeric attributes extracted from timing path graph nodes (e.g., delay, capacitance, drive strength).

### Graph-Level Features
Metadata from the entire timing path (e.g., total estimated delay, number of nodes, fanout count).

**Target variables** (from routing phase):
- `arrival_time` — Time at which a signal reaches an endpoint.
- `required_time` — Deadline for the signal to arrive to meet timing constraints.
- `slack` — Timing margin (positive or negative).

---

## 🧠 Model Architectures

### **`DeepGNN`**
A 2-layer Graph Convolutional Network:
1. **GCNConv → ReLU**
2. **GCNConv → ReLU**
3. **Global Mean Pooling**
4. **Linear Output Layer** (regression)

### **`WideAndDeepGNN`**
Combines node embeddings from a GNN (**deep path**) with raw graph-level features (**wide path**):
1. **Node Path** — Same as `DeepGNN`
2. **Graph Path** — Linear projection of graph-level features → ReLU
3. **Concatenate** both → Linear output layer

**Loss function** — Mean Squared Error (MSE)  
**Optimizer** — Adam (`lr=1e-3` by default)


## 🚀 How to Run

### 1️⃣ Activate Environment
```bash
cd <project_root>
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### 2️⃣ Run the Pipeline
```bash
python usecases/timing_prediction/main.py
```
