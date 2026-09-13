def interpret_vcdr(vcdr):
    """
    Applies clinical VCDR interpretation boundaries and guidelines matching the notebook exactly.
    Returns:
        tuple: (interpretation: str, recommendation: str)
    """
    if vcdr < 0.30:
        interpretation = "Small Physiological Cup"
        recommendation = "Routine ophthalmic examination."
    elif vcdr < 0.50:
        interpretation = "Normal Optic Disc"
        recommendation = "Continue routine eye screening."
    elif vcdr < 0.60:
        interpretation = "Borderline (0.5-0.6)"
        recommendation = "Regular follow-up and comprehensive glaucoma evaluation are recommended."
    elif vcdr < 0.70:
        interpretation = "Suspicious (>0.6)"
        recommendation = "Further clinical assessment and additional glaucoma tests are recommended."
    else:
        interpretation = "Highly Suspicious (>0.7)"
        recommendation = "Immediate comprehensive glaucoma evaluation is strongly recommended."
        
    return interpretation, recommendation
