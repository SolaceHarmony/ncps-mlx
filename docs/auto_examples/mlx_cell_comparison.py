"""Example comparing different MLX cell implementations."""

import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
from ncps.mlx import CTRNN, CTGRU, ELTC
from ncps.mlx.wirings import FullyConnected

# Generate sequence data
N = 1000  # sequence length
in_features = 2  # input dimension
out_features = 1  # output dimension
batch_size = 1  # using batch_size=1 for this example

# Generate input sequence: [batch_size, seq_length, features]
data_x = mx.stack([
    mx.sin(mx.linspace(0, 3 * mx.pi, N)), 
    mx.cos(mx.linspace(0, 3 * mx.pi, N))
], axis=1)  # Shape: [N, 2]
data_x = mx.expand_dims(data_x, axis=0)  # Shape: [1, N, 2]

# Generate target sequence: [batch_size, seq_length, output_dim]
data_y = mx.sin(mx.linspace(0, 6 * mx.pi, N))  # Shape: [N]
data_y = mx.reshape(data_y, (1, N, out_features))  # Shape: [1, N, 1]

# Generate time delta information: [batch_size, seq_length]
time_delta = mx.clip(mx.random.uniform(low=0.9, high=1.1, shape=(batch_size, N)), 0.9, 1.1)

# Initialize with explicit random seed for reproducibility
mx.random.seed(42)

# Create wiring
wiring = FullyConnected(units=8, output_dim=out_features)
wiring.build(in_features)

# Define model configurations
model_configs = [
    (
        "CTRNN",
        CTRNN(
            units=8,
            activation=mx.tanh,
            cell_clip=1.0
        )
    ),
    (
        "CTGRU",
        CTGRU(
            units=8,
            cell_clip=1.0
        )
    ),
    (
        "ELTC",
        ELTC(
            input_size=in_features,
            hidden_size=8,
            solver="rk4",
            ode_unfolds=6
        )
    )
]

# Define loss function
def mse_loss(y_pred, y_true):
    return mx.mean((y_pred - y_true) ** 2)

# Training configuration
training_config = {
    'num_epochs': 100,
    'learning_rate': 0.001,
    'max_grad_norm': 0.1,
    'max_grad_value': 1.0,
}

# Train each model configuration
for name, model in model_configs:
    print(f"\nTraining {name}")
    
    # Initialize optimizer
    optimizer = optim.Adam(
        learning_rate=training_config['learning_rate'],
        betas=[0.9, 0.999],
        eps=1e-8
    )
    
    # Define loss function that will be used for gradient computation
    def loss_fn(params):
        model.update(params)
        pred = model(data_x, time_delta=time_delta)
        return mse_loss(pred, data_y)
    
    # Training loop
    best_loss = float('inf')
    patience = 10
    patience_counter = 0
    
    for epoch in range(training_config['num_epochs']):
        # Compute loss and gradients
        loss, grads = mx.value_and_grad(loss_fn)(model.trainable_parameters())
        
        # Clip gradients
        grad_norm = mx.sqrt(sum(mx.sum(g * g) for _, g in mx.tree_flatten(grads)))
        if grad_norm > training_config['max_grad_norm']:
            scale = training_config['max_grad_norm'] / (grad_norm + 1e-6)
            grads = mx.tree_map(lambda g: g * scale, grads)
        
        # Update model parameters
        optimizer.update(model, grads)
        
        if mx.isnan(loss):
            print(f"Training {name} failed at epoch {epoch} with NaN loss.")
            break
        
        # Early stopping check
        if loss < best_loss:
            best_loss = loss
            patience_counter = 0
        else:
            patience_counter += 1
            
        if patience_counter >= patience:
            print(f"Early stopping triggered at epoch {epoch}")
            break
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch + 1}, Loss: {loss.item():.6f}")
            
        # Evaluate predictions periodically
        if (epoch + 1) % 50 == 0:
            pred = model(data_x, time_delta=time_delta)
            eval_loss = mse_loss(pred, data_y)
            print(f"Evaluation Loss: {eval_loss.item():.6f}")

print("\nTraining complete. Final losses:")
for name, model in model_configs:
    pred = model(data_x, time_delta=time_delta)
    final_loss = mse_loss(pred, data_y)
    print(f"{name}: {final_loss.item():.6f}")