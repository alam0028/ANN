# -*- coding: utf-8 -*-
"""Untitled2.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1cIK5ma1uH24izWrE6frMNLOH6rSqjy7W
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler


# Step 1: Load CSV Data

features_train_df = pd.read_csv("x_training.csv", index_col=0)
targets_train_df  = pd.read_csv("y_training.csv", index_col=0)
features_val_df   = pd.read_csv("x_val.csv", index_col=0)
targets_val_df    = pd.read_csv("y_val.csv", index_col=0)


# Step 2: Convert DataFrames to NumPy Arrays and Standardize

X_train_np = features_train_df.values.astype('float32')
y_train_np = targets_train_df.values.astype('float32')
X_val_np   = features_val_df.values.astype('float32')
y_val_np   = targets_val_df.values.astype('float32')

# Standardize features and targets
scaler_X = StandardScaler()
scaler_y = StandardScaler()

X_train = scaler_X.fit_transform(X_train_np)
X_val   = scaler_X.transform(X_val_np)
y_train = scaler_y.fit_transform(y_train_np)
y_val   = scaler_y.transform(y_val_np)

# Convert to torch tensors
X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
y_train_tensor = torch.tensor(y_train, dtype=torch.float32)
X_val_tensor   = torch.tensor(X_val, dtype=torch.float32)
y_val_tensor   = torch.tensor(y_val, dtype=torch.float32)

# Create DataLoader objects
batch_size = 32
train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
val_dataset   = TensorDataset(X_val_tensor, y_val_tensor)
train_loader  = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader    = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)


# Step 3: Define the Models


# Original Model: 5 hidden layers with 20 neurons each
class OriginalModel(nn.Module):
    def __init__(self, input_dim):
        super(OriginalModel, self).__init__()
        self.fc1 = nn.Linear(input_dim, 20)
        self.fc2 = nn.Linear(20, 20)
        self.fc3 = nn.Linear(20, 20)
        self.fc4 = nn.Linear(20, 20)
        self.fc5 = nn.Linear(20, 20)
        self.out = nn.Linear(20, 1)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.relu(self.fc3(x))
        x = self.relu(self.fc4(x))
        x = self.relu(self.fc5(x))
        x = self.out(x)
        return x

# New Model: 3 hidden layers with 20 neurons each
class NewModel(nn.Module):
    def __init__(self, input_dim):
        super(NewModel, self).__init__()
        self.fc1 = nn.Linear(input_dim, 20)
        self.fc2 = nn.Linear(20, 20)
        self.fc3 = nn.Linear(20, 20)
        self.out = nn.Linear(20, 1)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.relu(self.fc3(x))
        x = self.out(x)
        return x

input_dim = X_train_tensor.shape[1]  # e.g., input_dim = 10
orig_model = OriginalModel(input_dim)
new_model = NewModel(input_dim)


# Step 4: Print Model Parameter Counts

def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

orig_params = count_parameters(orig_model)
new_params  = count_parameters(new_model)

print(f"Original Model Parameters: {orig_params}")  # Expected ~1921 (if input_dim=10)
print(f"New Model Parameters: {new_params}")        # Expected ~1081 (if input_dim=10)


# Step 5: Define Training Function with Learning Rate Scheduler

def train_model(model, train_loader, val_loader, num_epochs=100, lr=1e-4, use_scheduler=True):
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    # Using ReduceLROnPlateau scheduler: reduces LR when a metric has stopped improving.
    if use_scheduler:
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=10, verbose=True)
    else:
        scheduler = None

    train_losses = []
    val_losses = []

    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        for inputs, targets in train_loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * inputs.size(0)
        epoch_train_loss = running_loss / len(train_loader.dataset)
        train_losses.append(epoch_train_loss)

        # Validation phase
        model.eval()
        running_val_loss = 0.0
        with torch.no_grad():
            for inputs, targets in val_loader:
                outputs = model(inputs)
                loss = criterion(outputs, targets)
                running_val_loss += loss.item() * inputs.size(0)
        epoch_val_loss = running_val_loss / len(val_loader.dataset)
        val_losses.append(epoch_val_loss)

        # Step the scheduler based on validation loss
        if scheduler is not None:
            scheduler.step(epoch_val_loss)

        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{num_epochs}: Train Loss = {epoch_train_loss:.4f}, Val Loss = {epoch_val_loss:.4f}")

    return train_losses, val_losses

# Step 6: Train Both Models

num_epochs = 100  # Adjust number of epochs as needed

print("\nTraining Original Model:")
orig_train_losses, orig_val_losses = train_model(orig_model, train_loader, val_loader, num_epochs=num_epochs)

print("\nTraining New Model:")
new_train_losses, new_val_losses = train_model(new_model, train_loader, val_loader, num_epochs=num_epochs)


# Step 7: Plot Training and Validation Loss Curves

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Plot for Original Model
axes[0].plot(orig_train_losses, label="Train Loss")
axes[0].plot(orig_val_losses, label="Val Loss")
axes[0].set_title("Original Model (5 Hidden Layers)")
axes[0].set_xlabel("Epoch")
axes[0].set_ylabel("MSE Loss")
axes[0].legend()
axes[0].grid(True)

# Plot for New Model
axes[1].plot(new_train_losses, label="Train Loss")
axes[1].plot(new_val_losses, label="Val Loss")
axes[1].set_title("New Model (3 Hidden Layers)")
axes[1].set_xlabel("Epoch")
axes[1].set_ylabel("MSE Loss")
axes[1].legend()
axes[1].grid(True)

plt.suptitle("Training and Validation Loss vs. Epoch")
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()