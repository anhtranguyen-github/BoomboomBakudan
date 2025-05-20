# Bitcoin Price Prediction Models

## Models Overview
This directory contains selected machine learning models for Bitcoin price prediction.
Training date: 2025-05-19

## Saved Models
LDA, GBM, XGB, CAT

## Model Details
- **Description**: Models trained on all technical indicators
- **Input features**: (see model_metadata_2025-05-19.json for complete list)
- **Output**: Binary classification (0 or 1)
  - 0: Price is expected to decrease
  - 1: Price is expected to increase

## Serving Instructions

### Preprocessing Requirements
1. Ensure all input features match the expected feature names
2. Handle missing values by forward-filling or using last valid values
3. No need for additional scaling as it's handled in model pipelines

### Prediction Code Example
```python
import joblib
import pandas as pd

# Load the model (use one of: LDA_full_2025-05-19.joblib, GBM_full_2025-05-19.joblib, XGB_full_2025-05-19.joblib, CAT_full_2025-05-19.joblib)
model = joblib.load('trained_models/LDA_full_2025-05-19.joblib')

# Prepare input data (example)
data = {...}  # Your input data with all required features
X = pd.DataFrame([data])

# Get prediction
prediction = model.predict(X)[0]
probability = model.predict_proba(X)[0][1]  # Probability of class 1

print(f"Prediction: {'Increase' if prediction == 1 else 'Decrease'}")
print(f"Confidence: {probability:.4f}")
```

See `model_metadata_2025-05-19.json` for complete feature lists and details.
