import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from analysis.models import Analysis
from .models import Clinician

def dashboard_home(request):
    """
    Renders the clinical workstation dashboard, computing metrics and listing recent scans,
    supporting filtering (by diagnosis and gender) and sorting options dynamically.
    """
    analyses = Analysis.objects.all()
    
    # 1. Capture dynamic filters from GET parameters
    diag = request.GET.get('diag', 'all')
    gender = request.GET.get('gender', 'all')
    sort = request.GET.get('sort', 'newest')
    
    # 2. Apply filters
    if diag == 'glaucoma':
        analyses = analyses.filter(diagnosis='Glaucoma')
    elif diag == 'normal':
        analyses = analyses.filter(diagnosis='Normal')
    elif diag == 'pending':
        analyses = analyses.filter(vcdr__isnull=True)
        
    if gender in ['Male', 'Female']:
        analyses = analyses.filter(patient__gender=gender)
        
    # 3. Apply sorting
    if sort == 'confidence_high':
        analyses = analyses.order_by('-confidence')
    elif sort == 'confidence_low':
        analyses = analyses.order_by('confidence')
    elif sort == 'vcdr_high':
        analyses = analyses.order_by('-vcdr')
    else: # newest
        analyses = analyses.order_by('-created_at')
        
    # Compute clinical metrics counts from base query (unfiltered for accurate stats cards)
    base_analyses = Analysis.objects.all()
    total_scans = base_analyses.count()
    suspects_count = base_analyses.filter(diagnosis='Glaucoma').count()
    normal_count = base_analyses.filter(diagnosis='Normal').count()
    pending_count = base_analyses.filter(vcdr__isnull=True).count()
    
    # Average speed / latency
    avg_processing_speed = 1.4 # seconds
    
    context = {
        'analyses': analyses[:10], # top 10 matching records
        'total_scans': total_scans,
        'suspects_count': suspects_count,
        'normal_count': normal_count,
        'pending_count': pending_count,
        'avg_processing_speed': avg_processing_speed,
    }
    return render(request, 'dashboard/home.html', context)

def update_clinician(request):
    """
    Handles POST requests from Settings Modal to modify clinician name and profile picture.
    """
    if request.method == 'POST':
        clinician, created = Clinician.objects.get_or_create(id=1)
        
        # 1. Update clinician name
        name = request.POST.get('name', '').strip()
        if name:
            clinician.name = name
            
        # 2. Handle profile picture deletion
        if request.POST.get('delete_picture') == 'true':
            if clinician.profile_picture:
                old_pic_path = clinician.profile_picture.path
                if os.path.exists(old_pic_path):
                    try:
                        os.remove(old_pic_path)
                    except Exception as e:
                        print(f"Failed to delete old profile picture file: {e}")
                clinician.profile_picture = None
                
        # 3. Handle new profile picture upload
        if request.FILES.get('profile_picture'):
            new_file = request.FILES['profile_picture']
            # Delete old profile picture on disk to avoid clutter
            if clinician.profile_picture:
                old_pic_path = clinician.profile_picture.path
                if os.path.exists(old_pic_path):
                    try:
                        os.remove(old_pic_path)
                    except Exception as e:
                        print(f"Failed to delete old profile picture file: {e}")
            clinician.profile_picture = new_file
            
        clinician.save()
        messages.success(request, "Clinician profile configurations updated successfully.")
        
    return redirect(request.META.get('HTTP_REFERER', 'dashboard:home'))

def coming_soon(request):
    """
    Renders the coming soon placeholder for future workstation expansions.
    """
    module_key = request.GET.get('module', 'generic')
    module_names = {
        'history': 'Patient History & Longitudinal Tracking',
        'batch': 'Batch Analysis & Processing Queue',
        'comparison': 'Neural Model Performance Comparison',
    }
    module_name = module_names.get(module_key, 'Requested Workspace Panel')
    
    context = {
        'module_key': module_key,
        'module_name': module_name,
    }
    return render(request, 'coming_soon.html', context)
