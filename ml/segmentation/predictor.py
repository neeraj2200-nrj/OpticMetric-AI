import os
import torch
import numpy as np
from .unet import build_unet

DEVICE = torch.device("cpu")

# Resolve model paths dynamically relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DISC_MODEL_PATH = os.path.join(BASE_DIR, 'best_disc_unet_512_v3.pth')
CUP_MODEL_PATH = os.path.join(BASE_DIR, 'best_cup_unet_512_v4.pth')

disc_model = None
cup_model = None

def init_models():
    """
    Loads PyTorch weights once, mapping them to the CPU.
    Raises FileNotFoundError if model checkpoints are missing.
    """
    global disc_model, cup_model
    if disc_model is not None and cup_model is not None:
        return
        
    if not os.path.exists(DISC_MODEL_PATH):
        raise FileNotFoundError(f"Optic Disc model checkpoint missing: {DISC_MODEL_PATH}")
    if not os.path.exists(CUP_MODEL_PATH):
        raise FileNotFoundError(f"Optic Cup model checkpoint missing: {CUP_MODEL_PATH}")
        
    disc_model = build_unet()
    disc_model.load_state_dict(torch.load(DISC_MODEL_PATH, map_location=DEVICE))
    disc_model.eval()
    
    cup_model = build_unet()
    cup_model.load_state_dict(torch.load(CUP_MODEL_PATH, map_location=DEVICE))
    cup_model.eval()

# Pre-initialize models on import
try:
    init_models()
except Exception as e:
    print(f"Warning: ML Segmentation models failed to load during startup: {e}")

def predict_probs(processed_image):
    """
    Infers raw probability maps (sigmoid outputs) from the preprocessed input.
    """
    global disc_model, cup_model
    if disc_model is None or cup_model is None:
        init_models()  # Retry loading models if they failed on import
        
    # Convert numpy array to 4D float tensor [1, 1, 512, 512]
    image_tensor = torch.tensor(processed_image, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
    
    with torch.no_grad():
        disc_logits = disc_model(image_tensor)
        cup_logits = cup_model(image_tensor)
        
        disc_probs = torch.sigmoid(disc_logits).squeeze().numpy()
        cup_probs = torch.sigmoid(cup_logits).squeeze().numpy()
        
    return disc_probs, cup_probs
