import numpy as np

def vertical_diameter(mask):
    """
    Computes the maximum vertical diameter (height) of the mask in pixels.
    """
    rows = np.where(mask > 0)[0]
    if len(rows) == 0:
        return 0
    return int(rows.max() - rows.min() + 1)

def horizontal_diameter(mask):
    """
    Computes the maximum horizontal diameter (width) of the mask in pixels.
    """
    cols = np.where(mask > 0)[1]
    if len(cols) == 0:
        return 0
    return int(cols.max() - cols.min() + 1)

def extract_features(disc_mask, cup_mask):
    """
    Extracts the 11 feature parameters in the exact order required by the Logistic Regression classifier.
    """
    disc_area = float(disc_mask.sum())
    cup_area = float(cup_mask.sum())
    rim_area = disc_area - cup_area
    
    disc_height = vertical_diameter(disc_mask)
    cup_height = vertical_diameter(cup_mask)
    disc_width = horizontal_diameter(disc_mask)
    cup_width = horizontal_diameter(cup_mask)
    
    vcdr = (
        cup_height / disc_height
        if disc_height > 0
        else 0.0
    )
    
    hcdr = (
        cup_width / disc_width
        if disc_width > 0
        else 0.0
    )
    
    cdar = (
        cup_area / disc_area
        if disc_area > 0
        else 0.0
    )
    
    rim_ratio = (
        rim_area / disc_area
        if disc_area > 0
        else 0.0
    )
    
    features = [
        disc_area,
        cup_area,
        rim_area,
        float(disc_height),
        float(cup_height),
        float(disc_width),
        float(cup_width),
        vcdr,
        hcdr,
        cdar,
        rim_ratio
    ]
    
    return features
