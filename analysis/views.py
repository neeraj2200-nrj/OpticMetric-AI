from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Patient, Analysis
from ml.inference import run_inference
from ml.classification.classifier import get_feature_importances
from ml.report_generation.clinical_report import interpret_vcdr
import random
import os

def image_analysis(request):
    """
    Renders the image upload dashboard and processing status pipeline.
    """
    return render(request, 'analysis/upload.html')

def upload_image(request):
    """
    Handles POST requests for new fundus uploads, saves them, triggers the ML interface,
    persists all extracted features and intermediate output paths, and redirects.
    """
    if request.method == 'POST' and request.FILES.get('fundus_image'):
        uploaded_file = request.FILES['fundus_image']
        
        # 1. Capture manual demographics from POST form
        name = request.POST.get('patient_name', '').strip()
        age_str = request.POST.get('patient_age', '').strip()
        gender = request.POST.get('patient_gender', '').strip()
        
        if not name or not age_str or not gender:
            messages.error(request, "Patient demographic configurations are incomplete.")
            return redirect('analysis:image_analysis')
            
        try:
            age = int(age_str)
        except ValueError:
            messages.error(request, "Invalid clinical input for patient age.")
            return redirect('analysis:image_analysis')
        
        # 2. Create Patient record using manual data
        random_suffix = random.randint(1000, 9999)
        patient_id = f"REF-T{random_suffix}"
        patient = Patient.objects.create(
            patient_id=patient_id,
            name=name,
            age=age,
            gender=gender
        )
        
        # 3. Create the temporary Analysis record to get the save path
        analysis = Analysis.objects.create(
            patient=patient,
            uploaded_image=uploaded_file,
            created_at=timezone.now()
        )
        
        # 4. Trigger the inference orchestrator pipeline
        results = run_inference(analysis.uploaded_image.path)
        
        # 5. Handle pipeline diagnostic errors
        if results.get('error') is not None:
            # Delete temporary records to keep DB clean
            analysis.delete()
            patient.delete()
            messages.error(
                request, 
                f"Clinical Pipeline Diagnostic Failure: {results.get('error')}. "
                f"Please verify model files and scan image integrity."
            )
            return redirect('analysis:image_analysis')
        
        # 6. Populate and persist all features and outputs in the database
        analysis.disc_mask = results['disc_mask']
        analysis.cup_mask = results['cup_mask']
        analysis.overlay_image = results['overlay_image']
        analysis.preprocessed_image = results['preprocessed_image']
        analysis.disc_prob_map = results['disc_prob_map']
        analysis.cup_prob_map = results['cup_prob_map']
        
        analysis.disc_area = results['disc_area']
        analysis.cup_area = results['cup_area']
        analysis.rim_area = results['rim_area']
        
        analysis.disc_height = results['disc_height']
        analysis.cup_height = results['cup_height']
        analysis.disc_width = results['disc_width']
        analysis.cup_width = results['cup_width']
        
        analysis.vcdr = results['vcdr']
        analysis.hcdr = results['hcdr']
        analysis.cdar = results['cdar']
        analysis.rim_ratio = results['rim_ratio']
        
        analysis.diagnosis = results['diagnosis']
        analysis.confidence = results['confidence']
        
        analysis.save()
        
        messages.success(request, "Ocular scan analyzed successfully by U-Net models.")
        return redirect('analysis:analysis_results', analysis_id=analysis.id)
        
    messages.error(request, "No image file provided.")
    return redirect('analysis:image_analysis')

def delete_analysis(request, analysis_id):
    """
    Handles POST requests to permanently delete a scan analysis record, patient record
    (if they have no other scans), and all related media artifacts on disk.
    """
    if request.method == 'POST':
        analysis = get_object_or_404(Analysis, id=analysis_id)
        patient = analysis.patient
        
        # Cache paths of files to delete from disk
        files_to_delete = []
        for field in [analysis.uploaded_image, analysis.disc_mask, analysis.cup_mask, 
                      analysis.overlay_image, analysis.preprocessed_image, 
                      analysis.disc_prob_map, analysis.cup_prob_map]:
            if field and field.name:
                files_to_delete.append(field.path)
                
        # Delete from database
        analysis.delete()
        
        # Check if the patient has other scans; delete patient if no scans remain
        if not patient.analyses.exists():
            patient.delete()
            
        # Clean files from disk
        for path in files_to_delete:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Failed to delete file on disk at {path}: {e}")
                    
        messages.success(request, "Patient scan analysis record deleted successfully.")
        
    return redirect('dashboard:home')

def analysis_results(request, analysis_id):
    """
    Displays the analysis detail page, rendering original fundus scans,
    masks, dynamic clinical charts, and classification metrics.
    """
    analysis = get_object_or_404(Analysis, id=analysis_id)
    
    disc_pct = 0.0
    cup_pct = 0.0
    rim_pct = 0.0
    if analysis.disc_area and analysis.disc_area > 0:
        cup_pct = (analysis.cup_area / analysis.disc_area) * 100.0
        disc_pct = 100.0 - cup_pct
        rim_pct = (analysis.rim_area / analysis.disc_area) * 100.0
        
    # Re-run the 5-classifier system dynamically on stored features
    clf_system_results = None
    if analysis.vcdr is not None:
        features_list = [
            analysis.disc_area,
            analysis.cup_area,
            analysis.rim_area,
            analysis.disc_height,
            analysis.cup_height,
            analysis.disc_width,
            analysis.cup_width,
            analysis.vcdr,
            analysis.hcdr,
            analysis.cdar,
            analysis.rim_ratio
        ]
        from ml.classification.classifier import classify_features_all
        try:
            clf_system_results = classify_features_all(features_list)
        except Exception as e:
            print(f"Error executing 5-Classifier System: {e}")
            
    # Get dynamic VCDR clinical category and recommendation guidelines
    clinical_category = "Pending Pipeline Execution"
    recommendation = "Pending clinical pipeline execution."
    if analysis.vcdr is not None:
        clinical_category, recommendation = interpret_vcdr(analysis.vcdr)
        
    # Set risk level alert styling tags
    risk_level = "info"
    if analysis.vcdr is not None:
        if analysis.vcdr < 0.30:
            risk_level = "success"  # Small Physiological Cup
        elif analysis.vcdr < 0.50:
            risk_level = "success"  # Normal
        elif analysis.vcdr < 0.60:
            risk_level = "warning"  # Borderline
        elif analysis.vcdr < 0.70:
            risk_level = "orange"   # Suspicious
        else:
            risk_level = "danger"   # High Risk / Highly Suspicious
            
    # If the client requests JSON (e.g. from an API call or frontend AJAX)
    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        from django.http import JsonResponse
        data = {
            "diagnosis": analysis.diagnosis,
            "confidence": analysis.confidence,
            "clf_system": clf_system_results,
            "features": {
                "disc_area": analysis.disc_area,
                "cup_area": analysis.cup_area,
                "rim_area": analysis.rim_area,
                "disc_height": analysis.disc_height,
                "cup_height": analysis.cup_height,
                "disc_width": analysis.disc_width,
                "cup_width": analysis.cup_width,
                "vcdr": analysis.vcdr,
                "hcdr": analysis.hcdr,
                "cdar": analysis.cdar,
                "rim_ratio": analysis.rim_ratio
            },
            "images": {
                "original": request.build_absolute_uri(analysis.uploaded_image.url) if analysis.uploaded_image else None,
                "disc_mask": request.build_absolute_uri(analysis.disc_mask.url) if analysis.disc_mask else None,
                "cup_mask": request.build_absolute_uri(analysis.cup_mask.url) if analysis.cup_mask else None,
                "overlay": request.build_absolute_uri(analysis.overlay_image.url) if analysis.overlay_image else None
            }
        }
        return JsonResponse(data)

    context = {
        'analysis': analysis,
        'is_completed': analysis.vcdr is not None,
        'disc_pct': disc_pct,
        'cup_pct': cup_pct,
        'rim_pct': rim_pct,
        'clf_results': clf_system_results,
        'clinical_category': clinical_category,
        'recommendation': recommendation,
        'risk_level': risk_level,
    }
    return render(request, 'analysis/results.html', context)
