# timingGCN
This is a cross-stage timing predictor.
It uses a GNN to predict the slacks at timing endpoints.

This script is based on the paper:

Zizheng Guo, Mingjie Liu, Jiaqi Gu, Shuhan Zhang, David Z. Pan, and Yibo Lin. 2022. A timing engine inspired graph neural network model for pre-routing slack prediction. In Proceedings of the 59th ACM/IEEE Design Automation Conference (DAC '22). Association for Computing Machinery, New York, NY, USA, 1207–1212. https://doi.org/10.1145/3489517.3530597

The source code from the paper was initially modified by Chih-Yu Lai <chihyul@mit.edu> to adapt for CircuitOps. The modified code is taken to create an example use case for CircuitOps.

## Usage
```
python3 main.py
```
