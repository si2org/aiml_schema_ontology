
# Usecases for Ontology  

The `usecases` folder contains use cases demonstrating how to utilize datagen utilities for ML applications. 

**Note:** These use cases are meant to show how you can use the data generation APIs in an ML training flow. 
The models themselves are just illustrative and haven’t been optimized for accuracy.

### Use Cases  

1. **[Arc Delay Predictor](./arc_delay_predictor)**  
   - Predicts arc delays of standard cells based on the input pin slew, load capacitance and cell type.

2. **[Pre-route Net Delay Predictor](./preroute_delay_predictor)**  
   - It is a cross-stage timing predictor which estimates net delays before routing.
   - This script is based on the paper:

   E. C. Barboza, N. Shukla, Y. Chen and J. Hu, "Machine Learning-Based Pre-Routing Timing Prediction with Reduced Pessimism," 2019 56th ACM/IEEE Design Automation Conference (DAC), Las Vegas, NV, USA, 2019, pp. 1-6.


3. **[Timing Graph Convolutional Network (GCN)](./timingGCN)**  
   - Leverages Graph Neural Networks (GNNs) to predict slacks at the endpoints of a design.  
   - This script is based on the paper:

   Zizheng Guo, Mingjie Liu, Jiaqi Gu, Shuhan Zhang, David Z. Pan, and Yibo Lin, "A timing engine inspired graph neural network model for pre-routing slack prediction," 2022 59th ACM/IEEE Design Automation Conference (DAC). https://doi.org/10.1145/3489517.3530597

---