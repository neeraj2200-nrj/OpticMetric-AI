import os
import joblib
import pandas as pd

# Resolve classifier path relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLASSIFIER_PATH = os.path.join(BASE_DIR, 'final_glaucoma_classifier_512.pkl')

classifier = None

def init_classifier():
    """
    Loads the Logistic Regression classifier pickle once using joblib.
    """
    global classifier
    if classifier is not None:
        return
        
    if not os.path.exists(CLASSIFIER_PATH):
        raise FileNotFoundError(f"Glaucoma classifier pickle missing: {CLASSIFIER_PATH}")
        
    classifier = joblib.load(CLASSIFIER_PATH)

# Pre-initialize classifier on import
try:
    init_classifier()
except Exception as e:
    print(f"Warning: ML Classifier failed to load during startup: {e}")

FEATURE_NAMES = [
    "Disc Area",
    "Cup Area",
    "Rim Area",
    "Disc Height",
    "Cup Height",
    "Disc Width",
    "Cup Width",
    "VCDR",
    "HCDR",
    "CDAR",
    "Rim Ratio"
]

def classify_features(features_list):
    """
    Constructs a DataFrame from the feature list and classifies it using the loaded Logistic Regression model.
    Returns:
        dict: prediction details and features importance ranks
    """
    global classifier
    if classifier is None:
        init_classifier()  # Retry loading classifier if it failed on import
        
    # Construct feature DataFrame
    feature_df = pd.DataFrame([features_list], columns=FEATURE_NAMES)
    
    # Predict class (0 = Normal, 1 = Glaucoma)
    prediction = int(classifier.predict(feature_df)[0])
    
    # Predict probabilities
    try:
        probability = classifier.predict_proba(feature_df)[0]
        normal_probability = float(probability[0] * 100.0)
        glaucoma_probability = float(probability[1] * 100.0)
        confidence_value = float(probability[prediction] * 100.0)
    except Exception:
        normal_probability = None
        glaucoma_probability = None
        confidence_value = None
        
    diagnosis_label = "Glaucoma" if prediction == 1 else "Normal"
    
    # Feature importances
    try:
        importances = classifier.feature_importances_
        feature_importances = []
        for name, imp in zip(FEATURE_NAMES, importances):
            feature_importances.append({
                "feature": name,
                "importance": float(imp)
            })
        # Sort descending
        feature_importances.sort(key=lambda x: x["importance"], reverse=True)
    except Exception:
        feature_importances = None
        
    return {
        "prediction": prediction,
        "diagnosis": diagnosis_label,
        "confidence": confidence_value,
        "normal_probability": normal_probability,
        "glaucoma_probability": glaucoma_probability,
        "feature_importances": feature_importances
    }

def get_feature_importances():
    """
    Retrieves the features sorted by Logistic Regression feature coefficient values.
    Returns:
        list: Sorted list of dicts with 'feature', 'importance'
    """
    global classifier
    if classifier is None:
        try:
            init_classifier()
        except Exception:
            return []
            
    if classifier is not None:
        try:
            importances = classifier.feature_importances_
            feature_imp = []
            for name, imp in zip(FEATURE_NAMES, importances):
                feature_imp.append({
                    'feature': name,
                    'importance': float(imp)
                })
            # Sort by importance descending
            feature_imp.sort(key=lambda x: x['importance'], reverse=True)
            return feature_imp
        except Exception:
            return []
    return []
