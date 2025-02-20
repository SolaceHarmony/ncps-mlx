"""Example of using liquid neural networks."""

import keras
import numpy as np
from ncps import ops
from ncps.layers.liquid import LiquidCell, CfCCell
from ncps.layers.rnn import RNN
from ncps.layers.layer import Dense, Sequential


def create_liquid_model(
    input_dim: int,
    hidden_dim: int,
    output_dim: int,
    backbone_units: int = 64,
    backbone_layers: int = 2,
    mode: str = "pure"
):
    """Create a model using liquid neurons.
    
    Args:
        input_dim: Input dimension
        hidden_dim: Hidden state dimension
        output_dim: Output dimension
        backbone_units: Units in backbone layers
        backbone_layers: Number of backbone layers
        mode: CfC mode ("pure", "gated", or "no_gate")
        
    Returns:
        Sequential model
    """
    # Create CfC cell
    cell = CfCCell(
        units=hidden_dim,
        activation="tanh",
        backbone_units=backbone_units,
        backbone_layers=backbone_layers,
        backbone_dropout=0.1,
        mode=mode,
        dtype="float32"
    )
    
    # Create RNN layer
    rnn = RNN(cell, return_sequences=False, dtype="float32")
    
    # Create model
    model = Sequential([
        rnn,
        Dense(output_dim, activation="linear", dtype="float32")
    ])
    
    return model


def generate_sequence_data(
    num_samples: int,
    seq_len: int,
    input_dim: int
):
    """Generate synthetic sequence data.
    
    Args:
        num_samples: Number of sequences
        seq_len: Length of each sequence
        input_dim: Input dimension
        
    Returns:
        Tuple of (inputs, time_deltas, targets)
    """
    # Generate random sequences
    x = np.random.normal(size=(num_samples, seq_len, input_dim)).astype(np.float32)
    
    # Generate random time deltas
    t = np.random.uniform(0.1, 1.0, size=(num_samples, seq_len, 1)).astype(np.float32)
    
    # Generate targets (sum of sequence)
    y = np.sum(x, axis=1).astype(np.float32)
    
    return x, t, y


def main():
    """Run example."""
    # Parameters
    batch_size = 32
    seq_len = 20
    input_dim = 16
    hidden_dim = 32
    output_dim = 16
    
    # Generate data
    x_train, t_train, y_train = generate_sequence_data(
        num_samples=1000,
        seq_len=seq_len,
        input_dim=input_dim
    )
    
    x_test, t_test, y_test = generate_sequence_data(
        num_samples=100,
        seq_len=seq_len,
        input_dim=input_dim
    )
    
    # Create model
    model = create_liquid_model(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        output_dim=output_dim,
        backbone_units=64,
        backbone_layers=2,
        mode="pure"
    )
    
    # Convert inputs to tensors
    x_train = ops.convert_to_tensor(x_train, dtype="float32")
    t_train = ops.convert_to_tensor(t_train, dtype="float32")
    y_train = ops.convert_to_tensor(y_train, dtype="float32")
    
    x_test = ops.convert_to_tensor(x_test, dtype="float32")
    t_test = ops.convert_to_tensor(t_test, dtype="float32")
    y_test = ops.convert_to_tensor(y_test, dtype="float32")
    
    # Process some data
    print("\nProcessing training data...")
    y_pred = model([x_train[:batch_size], t_train[:batch_size]])
    print(f"Input shape: {x_train.shape}")
    print(f"Time deltas shape: {t_train.shape}")
    print(f"Output shape: {y_pred.shape}")
    
    # Compute mean squared error
    mse = ops.reduce_mean(ops.square(y_pred - y_train[:batch_size]))
    print(f"Training MSE: {mse.numpy():.4f}")
    
    print("\nProcessing test data...")
    y_pred = model([x_test[:batch_size], t_test[:batch_size]])
    print(f"Input shape: {x_test.shape}")
    print(f"Time deltas shape: {t_test.shape}")
    print(f"Output shape: {y_pred.shape}")
    
    # Compute mean squared error
    mse = ops.reduce_mean(ops.square(y_pred - y_test[:batch_size]))
    print(f"Test MSE: {mse.numpy():.4f}")


if __name__ == "__main__":
    main()