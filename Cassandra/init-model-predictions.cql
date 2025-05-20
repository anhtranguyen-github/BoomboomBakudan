-- Create model_predictions table
USE assets;

-- Table for storing model predictions
CREATE TABLE IF NOT EXISTS model_predictions (
    id TEXT,               -- Same ID as the asset record
    asset_name TEXT,       -- Asset name (e.g., BTCUSDT)
    timestamp TIMESTAMP,   -- Timestamp of the original data point
    model_name TEXT,       -- Name of the model making the prediction
    prediction INT,        -- Binary prediction (0=decrease, 1=increase)
    probability FLOAT,     -- Probability of the prediction (confidence)
    predicted_at TIMESTAMP,-- When the prediction was made
    PRIMARY KEY ((asset_name, model_name), timestamp, predicted_at)
) WITH CLUSTERING ORDER BY (timestamp DESC, predicted_at DESC);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS model_predictions_id_idx ON model_predictions (id);
CREATE INDEX IF NOT EXISTS model_predictions_asset_idx ON model_predictions (asset_name);
CREATE INDEX IF NOT EXISTS model_predictions_model_idx ON model_predictions (model_name); 