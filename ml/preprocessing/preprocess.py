import cv2
import numpy as np

TARGET_SIZE = (512, 512)

def preprocess_image(image):
    """
    Applies Green channel extraction, CLAHE contrast enhancement,
    and [0, 1] normalization exactly as in the notebook.
    """
    # Resize to 512x512
    image_resized = cv2.resize(image, TARGET_SIZE)
    
    # Extract green channel
    green = image_resized[:, :, 1]
    
    # Apply CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    green_enhanced = clahe.apply(green.astype(np.uint8))
    
    # Normalize to [0, 1] float32
    processed = green_enhanced.astype(np.float32) / 255.0
    return processed
