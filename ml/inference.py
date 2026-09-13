import os
import time
import json
import cv2
import numpy as np
from django.conf import settings

from .preprocessing.preprocess import preprocess_image
from .segmentation.predictor import predict_probs
from .postprocessing import clean_masks
from .feature_extraction.features import extract_features
from .classification.classifier import classify_features

# Threshold values from the attached notebook
DISC_THRESHOLD = 0.50
CUP_THRESHOLD = 0.45

# Log file path
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inference.log')

def log_inference(filename, run_time, diagnosis, confidence, error=None):
    """
    Appends a JSON-structured log entry to ml/inference.log.
    """
    log_entry = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'filename': filename,
        'runtime_sec': float(f"{run_time:.4f}"),
        'diagnosis': diagnosis,
        'confidence': float(f"{confidence:.2f}") if confidence is not None else None,
        'error': str(error) if error else None
    }
    try:
        with open(LOG_FILE_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        print(f"Warning: Failed to write to inference log: {e}")

def run_inference(image_path):
    """
    Orchestrates the clinical processing pipeline:
      CLAHE preprocessing -> Sigmoid predictions -> Thresholding & Cleaning ->
      Overlay generation -> Feature extraction -> Logistic Regression classification -> Logging.
      
    Args:
        image_path (str): Absolute file path to the uploaded fundus scan.
        
    Returns:
        dict: A dictionary containing all diagnostic metrics and media paths.
    """
    start_time = time.time()
    filename = os.path.basename(image_path)
    name_no_ext, _ = os.path.splitext(filename)
    
    try:
        # 1. Load original image
        original_image = cv2.imread(image_path)
        if original_image is None:
            raise ValueError(f"Invalid uploaded image. Failed to decode file: {image_path}")
            
        # 2. Image Preprocessing (CLAHE + green channel resize to 512x512)
        processed_image = preprocess_image(original_image)
        
        # 3. Model Segmentations (Extract sigmoid probability maps)
        disc_probs, cup_probs = predict_probs(processed_image)
        
        # 4. Threshold maps
        pred_disc = (disc_probs > DISC_THRESHOLD).astype(np.float32)
        pred_cup = (cup_probs > CUP_THRESHOLD).astype(np.float32)
        
        # 5. Post-Processing cleaning (Morphology & interior constraint)
        clean_disc, clean_cup = clean_masks(pred_disc, pred_cup)
        
        # 6. Save Segmentations & Overlays inside MEDIA
        media_root = settings.MEDIA_ROOT
        
        # Define output directory paths
        disc_dir = os.path.join(media_root, 'results', 'disc')
        cup_dir = os.path.join(media_root, 'results', 'cup')
        overlay_dir = os.path.join(media_root, 'results', 'overlay')
        preproc_dir = os.path.join(media_root, 'results', 'preprocessed')
        prob_dir = os.path.join(media_root, 'results', 'prob_maps')
        
        # Create directories if missing
        os.makedirs(disc_dir, exist_ok=True)
        os.makedirs(cup_dir, exist_ok=True)
        os.makedirs(overlay_dir, exist_ok=True)
        os.makedirs(preproc_dir, exist_ok=True)
        os.makedirs(prob_dir, exist_ok=True)
        
        # Paths relative to MEDIA_ROOT (for Django ImageField/FileField)
        disc_rel = f"results/disc/{name_no_ext}_disc.png"
        cup_rel = f"results/cup/{name_no_ext}_cup.png"
        overlay_rel = f"results/overlay/{name_no_ext}_overlay.png"
        preproc_rel = f"results/preprocessed/{name_no_ext}_preprocessed.png"
        disc_prob_rel = f"results/prob_maps/{name_no_ext}_disc_prob.npy"
        cup_prob_rel = f"results/prob_maps/{name_no_ext}_cup_prob.npy"
        
        # Absolute file paths for writing
        disc_abs = os.path.join(media_root, disc_rel)
        cup_abs = os.path.join(media_root, cup_rel)
        overlay_abs = os.path.join(media_root, overlay_rel)
        preproc_abs = os.path.join(media_root, preproc_rel)
        disc_prob_abs = os.path.join(media_root, disc_prob_rel)
        cup_prob_abs = os.path.join(media_root, cup_prob_rel)
        
        # Save U-Net masks
        cv2.imwrite(disc_abs, clean_disc * 255)
        cv2.imwrite(cup_abs, clean_cup * 255)
        
        # Generate Overlay (BGR Green [0,255,0] for disc, BGR Red [0,0,255] for cup)
        background = cv2.resize(original_image, (512, 512))
        overlay = background.copy()
        overlay[clean_disc == 1] = [0, 255, 0]
        overlay[clean_cup == 1] = [0, 0, 255]
        cv2.imwrite(overlay_abs, overlay)
        
        # Save preprocessed image (contrast equalized green channel)
        cv2.imwrite(preproc_abs, (processed_image * 255).astype(np.uint8))
        
        # Save raw probability maps (.npy) for debugging/threshold tuning
        np.save(disc_prob_abs, disc_probs)
        np.save(cup_prob_abs, cup_probs)
        
        # 7. Feature Extraction
        features = extract_features(clean_disc, clean_cup)
        
        # 8. 5-Classifier Glaucoma Prediction System Classification
        from .classification.classifier import classify_features_all
        clf_results = classify_features_all(features)
        diagnosis = clf_results.get("diagnosis")
        confidence = clf_results.get("confidence")
        
        # Log successful inference
        run_time = time.time() - start_time
        log_inference(filename, run_time, diagnosis, confidence)
        
        # Assemble results dictionary
        return {
            'disc_mask': disc_rel,
            'cup_mask': cup_rel,
            'overlay_image': overlay_rel,
            'preprocessed_image': preproc_rel,
            'disc_prob_map': disc_prob_rel,
            'cup_prob_map': cup_prob_rel,
            'disc_area': features[0],
            'cup_area': features[1],
            'rim_area': features[2],
            'disc_height': int(features[3]),
            'cup_height': int(features[4]),
            'disc_width': int(features[5]),
            'cup_width': int(features[6]),
            'vcdr': features[7],
            'hcdr': features[8],
            'cdar': features[9],
            'rim_ratio': features[10],
            'diagnosis': diagnosis,
            'confidence': confidence,
            'models': clf_results.get('models'),
            'majority_voting': clf_results.get('majority_voting'),
            'primary_model': clf_results.get('primary_model'),
            'probability_aggregation': clf_results.get('probability_aggregation'),
            'error': None
        }
        
    except Exception as e:
        run_time = time.time() - start_time
        log_inference(filename, run_time, 'Error', None, error=e)
        return {
            'disc_mask': None,
            'cup_mask': None,
            'overlay_image': None,
            'preprocessed_image': None,
            'disc_prob_map': None,
            'cup_prob_map': None,
            'disc_area': None,
            'cup_area': None,
            'rim_area': None,
            'disc_height': None,
            'cup_height': None,
            'disc_width': None,
            'cup_width': None,
            'vcdr': None,
            'hcdr': None,
            'cdar': None,
            'rim_ratio': None,
            'diagnosis': 'Error',
            'confidence': None,
            'models': None,
            'majority_voting': None,
            'primary_model': None,
            'probability_aggregation': None,
            'error': str(e)
        }
