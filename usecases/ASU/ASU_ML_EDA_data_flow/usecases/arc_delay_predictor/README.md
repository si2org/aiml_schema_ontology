# Arc delay predictor
It is a simple random forest regressor based model that predicts the worst-case arc delay with input slew, load capacitance and cell type as it's input features. 

This script is developed mainly to provide an example on how to use datagen APIs for dataset generation using the schema. However it can also be used to replace the lookup table based arc delay extraction with an estimator that is differentiable.

- **Features**: Target input pin slew, output pin load capacitance, cell type
- **Labels**: Worst-case arc delay


## Usage
```
python3 arc_delay_prediction.py
```
