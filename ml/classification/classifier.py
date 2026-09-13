import os
import joblib
import pandas as pd

# Resolve classification directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CLASSIFIER_CONFIGS = {
    'logistic_regression': {
        'name': 'Logistic Regression',
        'file': 'logistic_regression.pkl'
    },
    'svm': {
        'name': 'Support Vector Machine (SVM)',
        'file': 'svm.pkl'
    },
    'xgboost': {
        'name': 'XGBoost',
        'file': 'xgboost.pkl'
    },
    'mlp': {
        'name': 'Multi-Layer Perceptron (MLP)',
        'file': 'mlp.pkl'
    },
    'extra_trees': {
        'name': 'Extra Trees',
        'file': 'extra_trees.pkl'
    }
}

classifiers = {}

def init_classifiers():
    """
    Loads all five pre-trained classifier pickle files using joblib.
    """
    global classifiers
    if len(classifiers) == len(CLASSIFIER_CONFIGS):
        return
        
    for key, config in CLASSIFIER_CONFIGS.items():
        if key not in classifiers:
            model_path = os.path.join(BASE_DIR, config['file'])
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Classifier model checkpoint missing: {model_path}")
            classifiers[key] = joblib.load(model_path)

# Pre-initialize classifiers on import
try:
    init_classifiers()
except Exception as e:
    print(f"Warning: ML Classifiers failed to load during startup: {e}")

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

def classify_features_all(features_list, primary_key='logistic_regression'):
    """
    Passes the 11-feature vector independently through all FIVE trained classifiers:
      1. Logistic Regression
      2. Support Vector Machine (SVM)
      3. XGBoost
      4. Multi-Layer Perceptron (MLP)
      5. Extra Trees

    Computes:
      - Option 1: All Models Independently
      - Option 2: Majority Voting
      - Option 3: Primary Model
      - Option 4: Probability Aggregation

    Returns:
      dict: Structured results for all 5 models and 4 prediction filter modes.
    """
    global classifiers
    if len(classifiers) < len(CLASSIFIER_CONFIGS):
        init_classifiers()

    # Construct 11-feature DataFrame matching exact column order expected by classifiers
    feature_df = pd.DataFrame([features_list], columns=FEATURE_NAMES)

    models_results = []
    models_dict = {}

    for key, config in CLASSIFIER_CONFIGS.items():
        clf = classifiers[key]
        
        # Predict class (0 = Normal, 1 = Glaucoma)
        prediction = int(clf.predict(feature_df)[0])
        diagnosis_label = "Glaucoma" if prediction == 1 else "Normal"
        
        # Predict probabilities
        try:
            prob = clf.predict_proba(feature_df)[0]
            normal_prob = float(prob[0] * 100.0)
            glaucoma_prob = float(prob[1] * 100.0)
            confidence_val = float(prob[prediction] * 100.0)
        except Exception:
            normal_prob = 50.0
            glaucoma_prob = 50.0
            confidence_val = 50.0

        model_res = {
            'key': key,
            'name': config['name'],
            'prediction': prediction,
            'diagnosis': diagnosis_label,
            'confidence': confidence_val,
            'normal_probability': normal_prob,
            'glaucoma_probability': glaucoma_prob
        }
        models_results.append(model_res)
        models_dict[key] = model_res

    # ----------------------------------------------------
    # Filter 1: All Models Independently (Default)
    # ----------------------------------------------------
    # List of all 5 individual model outputs (models_results)

    # ----------------------------------------------------
    # Filter 2: Majority Voting
    # ----------------------------------------------------
    glaucoma_votes = sum(1 for m in models_results if m['prediction'] == 1)
    normal_votes = 5 - glaucoma_votes
    majority_pred = 1 if glaucoma_votes >= 3 else 0
    majority_diag = "Glaucoma" if majority_pred == 1 else "Normal"
    winning_votes = glaucoma_votes if majority_pred == 1 else normal_votes
    vote_text = f"{winning_votes} / 5 models -> {majority_diag}"

    majority_voting = {
        'prediction': majority_pred,
        'diagnosis': majority_diag,
        'glaucoma_votes': glaucoma_votes,
        'normal_votes': normal_votes,
        'vote_text': vote_text
    }

    # ----------------------------------------------------
    # Filter 3: Primary Model
    # ----------------------------------------------------
    if primary_key not in models_dict:
        primary_key = 'logistic_regression'
    selected_primary = models_dict[primary_key]

    primary_model = {
        'selected_key': primary_key,
        'name': selected_primary['name'],
        'prediction': selected_primary['prediction'],
        'diagnosis': selected_primary['diagnosis'],
        'confidence': selected_primary['confidence'],
        'normal_probability': selected_primary['normal_probability'],
        'glaucoma_probability': selected_primary['glaucoma_probability']
    }

    # ----------------------------------------------------
    # Filter 4: Probability Aggregation
    # ----------------------------------------------------
    avg_glaucoma_prob = sum(m['glaucoma_probability'] for m in models_results) / 5.0
    avg_normal_prob = 100.0 - avg_glaucoma_prob
    agg_pred = 1 if avg_glaucoma_prob >= 50.0 else 0
    agg_diag = "Glaucoma" if agg_pred == 1 else "Normal"
    agg_confidence = avg_glaucoma_prob if agg_pred == 1 else avg_normal_prob

    probability_aggregation = {
        'label': 'Aggregated Model Score',
        'prediction': agg_pred,
        'diagnosis': agg_diag,
        'aggregated_score': avg_glaucoma_prob,
        'confidence': agg_confidence,
        'normal_probability': avg_normal_prob,
        'glaucoma_probability': avg_glaucoma_prob
    }

    # Top level diagnosis/confidence defaults to Majority Voting
    return {
        'diagnosis': majority_diag,
        'confidence': majority_voting['glaucoma_votes'] / 5.0 * 100.0,
        'models': models_results,
        'models_dict': models_dict,
        'majority_voting': majority_voting,
        'primary_model': primary_model,
        'probability_aggregation': probability_aggregation
    }

# Backward compatibility alias
def classify_features(features_list):
    return classify_features_all(features_list)

def get_feature_importances(model_key='logistic_regression'):
    """
    Retrieves feature importances for models that expose coefficients or importances.
    """
    global classifiers
    if len(classifiers) < len(CLASSIFIER_CONFIGS):
        try:
            init_classifiers()
        except Exception:
            return []
            
    clf = classifiers.get(model_key)
    if clf is None:
        clf = classifiers.get('logistic_regression')
        
    if clf is not None:
        try:
            # Check for Pipeline vs raw estimator
            estimator = clf.named_steps['classifier'] if hasattr(clf, 'named_steps') and 'classifier' in clf.named_steps else clf
            if hasattr(clf, 'named_steps') and hasattr(clf, 'steps'):
                estimator = clf.steps[-1][1]

            if hasattr(estimator, 'feature_importances_'):
                importances = estimator.feature_importances_
            elif hasattr(estimator, 'coef_'):
                importances = abs(estimator.coef_[0])
            else:
                importances = None
                
            if importances is not None:
                feature_imp = []
                for name, imp in zip(FEATURE_NAMES, importances):
                    feature_imp.append({
                        'feature': name,
                        'importance': float(imp)
                    })
                feature_imp.sort(key=lambda x: x['importance'], reverse=True)
                return feature_imp
        except Exception:
            pass
    return []
