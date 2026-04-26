import torch
import torch.nn as nn
import os

class CoastalPINN(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(2, 128),
            nn.Tanh(),
            nn.Linear(128, 128),
            nn.Tanh(),
            nn.Linear(128, 1)
        )

    def forward(self, x):
        return self.network(x)

def compute_physics_loss(model, elevation, lat):
    elevation.requires_grad_(True)
    lat.requires_grad_(True)
    
    x = torch.cat([elevation, lat], dim=1)
    predicted_loss = model(x)
    
    loss_gradient = torch.autograd.grad(
        predicted_loss, 
        elevation, 
        grad_outputs=torch.ones_like(predicted_loss), 
        create_graph=True
    )[0]
    
    physics_residual = loss_gradient + (0.1 * elevation)
    return torch.mean(physics_residual**2)

model = CoastalPINN()

weights_path = "trained_pinn_weights.pth"
if os.path.exists(weights_path):
    model.load_state_dict(torch.load(weights_path, map_location=torch.device('cpu'), weights_only=True))

model.eval()

def predict_land_loss(elevation: float, lat: float):
    e_tensor = torch.tensor([[elevation]], dtype=torch.float32)
    l_tensor = torch.tensor([[lat]], dtype=torch.float32)
    x = torch.cat([e_tensor, l_tensor], dim=1)
    
    with torch.no_grad():
        prediction = model(x).item()
        
    return round(max(0.0, prediction), 1)