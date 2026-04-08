# Length Prediction — Neural Network for Net Wire Length Estimation

This module demonstrates how to use **pre-routing placement features** from an Electronic Design Automation (EDA) flow to **predict final routed net lengths** using a feedforward neural network (FNN).  

It builds on the `eda_schema_ontology.py` utilities to load and merge relevant features from the **placement** and **routing** phases of a VLSI design flow.

---

## 📌 Context in the AIML_Schema_Ontology Project

This is one of the machine learning use cases in the [`AIML_Schema_Ontology`](../../README.md) repository:

- **Goal** — Predict `netLength` *before* running the full routing process.
- **Data Source** — Ontology-based datasets generated from detailed placement and detailed routing design phases.
- **Benefit** — Provides early estimates for design quality, enabling optimization and routing-aware placement without full routing runs.

---

## 📂 Folder Structure

```
usecases/length_prediction/
├── data.py         # Data loading and preprocessing
├── model.py        # PyTorch FNN definition (NetLengthPredictor)
├── train_eval.py   # Training and evaluation loops
└── main.py         # Pipeline entry point
```

---

## 🔍 Features Used

The model uses **two placement-phase features** for each net:

| Feature Name     | Description |
|------------------|-------------|
| `estimatedHpwl`  | Estimated Half-Perimeter Wire Length from placement |
| `numFanout`      | Number of sinks connected to the net |

**Target variable**:  
- `netLength` — Measured final net length from detailed routing.

---

## 🧠 Model Architecture

**`NetLengthPredictor`** (Feedforward Neural Network):

1. **Input layer** — 2 features (`estimatedHpwl`, `numFanout`)
2. **Hidden layer 1** — 32 neurons, ReLU activation
3. **Hidden layer 2** — 16 neurons, ReLU activation
4. **Output layer** — 1 neuron (predicted net length)

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
python usecases/length_prediction/main.py
```
