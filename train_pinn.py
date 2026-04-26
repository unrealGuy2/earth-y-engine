import torch
import torch.nn as nn
import torch.optim as optim
from pinn_model import CoastalPINN, compute_physics_loss

def generate_training_data(samples=5000):
    elevations = torch.rand(samples, 1) * 20.0 
    lats = torch.rand(samples, 1) * 180.0 - 90.0
    
    base_erosion = torch.clamp((15.0 - elevations) * 1.2, min=0.0)
    latitude_effect = torch.abs(torch.cos(torch.deg2rad(lats))) * 2.0
    
    actual_loss = base_erosion + latitude_effect + (torch.randn(samples, 1) * 0.5)
    return elevations, lats, actual_loss

def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on: {device}")
    
    model = CoastalPINN().to(device)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    elevations, lats, actual_loss = generate_training_data()
    elevations, lats, actual_loss = elevations.to(device), lats.to(device), actual_loss.to(device)
    
    epochs = 2000
    
    for epoch in range(epochs):
        optimizer.zero_grad()
        
        inputs = torch.cat([elevations, lats], dim=1)
        predictions = model(inputs)
        
        data_loss = nn.MSELoss()(predictions, actual_loss)
        
        physics_loss = compute_physics_loss(model, elevations, lats)
        
        total_loss = data_loss + (0.5 * physics_loss)
        
        total_loss.backward()
        optimizer.step()
        
        if epoch % 200 == 0:
            print(f"Epoch {epoch} | Data Loss: {data_loss.item():.4f} | Physics Loss: {physics_loss.item():.4f}")
            
    torch.save(model.state_dict(), "trained_pinn_weights.pth")
    print("Training Complete. Weights saved to trained_pinn_weights.pth")

if __name__ == "__main__":
    train()