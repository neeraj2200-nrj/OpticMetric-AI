import cv2
import numpy as np

def largest_component(mask):
    """
    Cleans binary mask to preserve only the largest connected component.
    """
    mask = mask.astype(np.uint8)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask,
        connectivity=8
    )
    if num_labels <= 1:
        return mask
        
    largest_label = 1 + np.argmax(
        stats[1:, cv2.CC_STAT_AREA]
    )
    cleaned = np.zeros_like(mask)
    cleaned[labels == largest_label] = 1
    return cleaned

def fill_holes(mask):
    """
    Fills inner holes in the binary mask using morphological closing.
    """
    kernel = np.ones((5, 5), np.uint8)
    return cv2.morphologyEx(
        mask.astype(np.uint8),
        cv2.MORPH_CLOSE,
        kernel
    )

def clean_masks(pred_disc, pred_cup):
    """
    Applies largest component and closing morphology, then enforces
    that the predicted cup lies entirely inside the predicted disc.
    """
    clean_disc = largest_component(pred_disc)
    clean_disc = fill_holes(clean_disc)
    
    clean_cup = largest_component(pred_cup)
    clean_cup = fill_holes(clean_cup)
    
    # Enforce cup inside disc constraint
    clean_cup = clean_cup * clean_disc
    
    return clean_disc, clean_cup
